# serializers.py
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Product, Order, User, Cart, CartItem, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'product','is_main']

    def get_image(self, obj):
        if not obj.image:
            return None
        
        name = str(obj.image.name)
        # Handle cases where Django prepends 'products/' to the URL
        if "http://" in name or "https://" in name:
            idx = name.find("http")
            return name[idx:]
        
        if name.startswith('data:'):
            return name
        
        try:
            url = obj.image.url
            request = self.context.get('request')
            if request is not None and not url.startswith('http'):
                return request.build_absolute_uri(url)
            return url
        except (ValueError, AttributeError):
            return None
        
        
class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'code', 'name', 'description', 'price', 'quantity', 'images', 'brand', 'category']
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        request= self.context.get('request')
        images_data = request.FILES.getlist('images')
        
        # Debug logging
        print("=== DEBUG CREATE PRODUCT ===")
        print(f"FILES keys: {list(request.FILES.keys())}")
        print(f"FILES: {request.FILES}")
        print(f"images_data from 'images': {images_data}")
        
        # Also check for 'image' (singular) as fallback
        if not images_data:
            single_image = request.FILES.get('image')
            if single_image:
                images_data = [single_image]
                print(f"Found single image: {single_image}")
        
        product = Product.objects.create(**validated_data)
        for index,image_file in enumerate(images_data):
            print(f"Creating ProductImage for: {image_file}")
            ProductImage.objects.create(product=product, image=image_file, is_main=index==0)
        
        print(f"Total images created: {len(images_data)}")
        return product
        

    def update(self, instance, validated_data):
        request=self.context.get('request')
        images_data = request.FILES.getlist('images')
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if images_data:
            for image_file in images_data:
                ProductImage.objects.create(product=instance, image=image_file)
        return instance
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','first_name', 'last_name', 'username', 'email', 'date_birth','password', 'role', 'created_at', 'is_staff', 'is_active']
        read_only_fields = ['created_at', 'is_staff', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate_role(self, value):
        """Only admins can set/change roles"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # If user is not admin, they cannot change role
            if not request.user.role == 'ADMIN':
                # For updates, keep existing role
                if self.instance:
                    return self.instance.role
                # For new users, default to CUSTOMER
                return 'CUSTOMER'
        return value
        
    def create(self, validated_data):
        password = validated_data.pop('password')
        user= User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user
        
class CartItemSerializer(serializers.ModelSerializer):
    product_name=serializers.CharField(source='product.name', read_only=True)
    price=serializers.DecimalField(source='current_price', max_digits=10, decimal_places=2, read_only=True)
    subtotal=serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'product_name', 'quantity', 'subtotal','price']
        read_only_fields = ['subtotal','price']
        
    def create(self, validated_data):
        cart=validated_data.get('cart')
        product=validated_data.get('product')
        quantity=validated_data.get('quantity')
        
        try:
            cart_item, created=CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': quantity})
            if not created:
                cart_item.quantity += quantity
            cart_item.full_clean()
            cart_item.save()
            return cart_item
        except DjangoValidationError as e:
            raise serializers.ValidationError(getattr(e,'message_dict', e.messages))
    
    def validate_quantity(self,value):
        if value<1:
            raise serializers.ValidationError("La cantidad debe ser al menos 1")
        return value
    
    
class CartSerializer(serializers.ModelSerializer):
    items=CartItemSerializer(many=True, read_only=True)
    total_items=serializers.IntegerField(source='items.count', read_only=True)
    total_price=serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'total_items', 'total_price', 'items', 'created_at', 'updated_at']
        read_only_fields = ['user']
        
class OrderSerializer(serializers.ModelSerializer):
    product_name=serializers.CharField(source='product.name', read_only=True)

    
    class Meta:
        model = Order
        fields = ['id', 'product', 'product_name', 'quantity', 'total', 'created_at', 'updated_at']
        read_only_fields = ['total', 'created_at', 'updated_at']
        
    def create(self, validated_data):
        return super().create(validated_data)