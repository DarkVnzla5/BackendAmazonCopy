from rest_framework import viewsets, serializers, permissions, parsers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from .models import Product, Cart, CartItem, User, Order, ProductImage
from .serializers import (ProductSerializer, CartSerializer, CartItemSerializer, UserSerializer, OrderSerializer, ProductImageSerializer)


class ProductViewSet(viewsets.ModelViewSet):
    queryset=Product.objects.all().order_by('-created_at')
    serializer_class=ProductSerializer
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    parser_classes=[parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

class ProductImageViewSet(viewsets.ModelViewSet):
    queryset=ProductImage.objects.all()
    serializer_class=ProductImageSerializer
    permission_classes=[permissions.IsAuthenticatedOrReadOnly]
    parser_classes=[parsers.MultiPartParser, parsers.FormParser]
    
    def get_queryset(self):
        product_id = self.request.query_params.get('product_id', None)
        if product_id is not None:
            return self.queryset.filter(product__id=product_id)
        return self.queryset
    
class OrderViewSet(viewsets.ModelViewSet):
    queryset=Order.objects.select_related('product').all().order_by('-created_at')
    serializer_class=OrderSerializer
    permission_classes=[permissions.IsAuthenticated]
    
class UserViewSet(viewsets.ModelViewSet):
    queryset=User.objects.all()
    serializer_class=UserSerializer
    
    def get_permissions(self):
        """
        Instantiate and return the list of permissions that this view requires.
        """
        from .permissions import CanManageUsers, IsAdminUser
        
        if self.action in ['create']:
            # Anyone can create an account (register)
            permission_classes = [permissions.AllowAny]
        elif self.action in ['assign_role', 'destroy']:
            # Only admins can assign roles or delete users
            permission_classes = [IsAdminUser]
        else:
            # For list, retrieve, update, partial_update
            permission_classes = [CanManageUsers]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filter queryset based on user role:
        - Admins see all users
        - Staff see all users (read-only via permissions)
        - Customers only see themselves
        """
        user = self.request.user
        
        if not user.is_authenticated:
            return User.objects.none()
        
        if user.role == 'ADMIN' or user.role == 'STAFF':
            return User.objects.all()
        
        # Customers only see their own profile
        return User.objects.filter(pk=user.pk)
    
    def get_serializer_context(self):
        """Pass request context to serializer for role validation"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def assign_role(self, request, pk=None):
        """
        Admin-only endpoint to assign roles to users.
        POST /api/users/{id}/assign_role/
        Body: {"role": "ADMIN"|"STAFF"|"CUSTOMER"}
        """
        if request.user.role != 'ADMIN':
            return Response(
                {"detail": "Only admins can assign roles."},
                status=403
            )
        
        user = self.get_object()
        new_role = request.data.get('role')
        
        if new_role not in ['ADMIN', 'STAFF', 'CUSTOMER']:
            return Response(
                {"detail": "Invalid role. Must be ADMIN, STAFF, or CUSTOMER."},
                status=400
            )
        
        user.role = new_role
        user.save()
        
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
class CartViewSet(viewsets.ModelViewSet):
    queryset= Cart.objects.all()
    serializer_class=CartSerializer
    permission_classes=[permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Cart.objects.all()
        return Cart.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    @action(detail=False, methods=['get'])
    def current_cart(self,request):
        try:
            cart=Cart.objects.get_or_create(user=request.user)
            serializer=self.get_serializer(cart)
            return Response(serializer.data)
        except Cart.DoesNotExist:
            return Response({"detail":"No active cart found."}, status=404) 
    
class CartItemViewSet(viewsets.ModelViewSet):
    queryset=CartItem.objects.select_related('cart', 'product').all()
    serializer_class=CartItemSerializer
    permission_classes=[permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return self.queryset.all()
        return CartItem.objects.select_related('product').filter(cart__user=self.request.user)
    
    def perform_create(self, serializer):
        user=self.request.user
        product_id=self.request.data.get('product_id') or self.request.data.get('product')
        try:
            quantity=int(self.request.data.get('quantity', 1))
            if quantity<=0:
                raise ValueError("Quantity must be a positive.")
        except ValueError:
            raise serializers.ValidationError({"quantity":"Quantity must be a valid number."})
        
        cart, _ =Cart.objects.get_or_create(user=user)
        try:
            product=Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            raise serializers.ValidationError({"product_id:":"Product does not exist"})
        try:
            cart_item=CartItem.objects.get(cart=cart, product=product)
            cart_item.quantity+=int(quantity)
            cart_item.clean()
            cart_item.save()
            response_serializer=self.get_serializer(cart_item)
            return Response(response_serializer.data, status=200)
                    
        except CartItem.DoesNotExist:
            try:
                serializer.save(cart=cart, product=product, quantity=quantity, current_price=product.price)
            except ValidationError as e:
                error_detail=e.message_dict if hasattr(e, 'message_dict') else {'detail': e.messages}
                raise serializers.ValidationError({"validation_error": error_detail})
    
    def perform_update(self, serializer):
        try:
            serializer.save()
        except ValidationError as e:
            error_detail=e.message_dict if hasattr(e, 'message_dict') else {'detail': e.messages}
            raise serializers.ValidationError({"validation_error": error_detail})
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=204)

from rest_framework_simplejwt.tokens import RefreshToken

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    Custom login view that returns user data and JWT tokens.
    """
    email = request.data.get('email')
    password = request.data.get('password')

    if not email or not password:
        return Response({"message": "Email y contraseña son requeridos"}, status=400)

    try:
        user_object = User.objects.get(email=email)
        user = authenticate(username=user_object.username, password=password)
    except User.DoesNotExist:
        return Response({"message": "Usuario no encontrado"}, status=404)
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            "id": user.id,
            "email": user.email,
            "name": f"{user.first_name} {user.last_name}",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        })
    else:
        return Response({"message": "Credenciales inválidas"}, status=401)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_view(request):
    """
    Mock dashboard data for the frontend charts.
    """
    data = {
        "sales": [65, 59, 80, 81, 56, 55, 40],
        "buys": [28, 48, 40, 19, 86, 27, 90],
        "stock": [300, 50, 100, 150, 200, 250, 300],
        "spends": [40, 44, 55, 57, 56, 61, 58],
        "labels": ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio"]
    }
    return Response(data)
    
        