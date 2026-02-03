from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser

class Product(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    brand = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        if self.quantity < 0:
            raise ValidationError("La cantidad no puede ser negativa")
    def date(self):
        return self.created_at.strftime("%d/%m/%Y %H:%M")

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', max_length=500)
    is_main = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Imagen de{self.product.name}"

class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Orden {self.id} - {self.product.name} x {self.quantity}" 
    
    def clean(self):
        if self.quantity > self.product.quantity:
            raise ValidationError("No hay suficiente stock para completar la orden")
    
    def save(self, *args, **kwargs):
        self.total = self.product.price * self.quantity
        super().save(*args, **kwargs)

class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('STAFF', 'Staff'),
        ('CUSTOMER', 'Customer'),
    ]
    
    email = models.EmailField(unique=True)
    date_birth = models.DateField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CUSTOMER')
    created_at = models.DateTimeField(auto_now_add=True)
    
    # We remove explicit first_name, last_name, username, password, is_staff, is_active
    # as they are inherited from AbstractUser.
    
    # We can keep related_name args if needed to avoid conflicts if we were using default User too,
    # but since we are replacing it, it's fine.
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        return self.role == 'ADMIN'
    
    def is_customer(self):
        return self.role == 'CUSTOMER'
    
    def is_staff_member(self):
        return self.role == 'STAFF'

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='CartItem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Carrito de {self.user.first_name} {self.user.last_name}"
    
    @property
    def total_items(self):
        return self.cartitem_set.aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def total_price(self):
        total = 0
        for item in self.cartitem_set.all():
            total += item.quantity * item.current_price
        return total

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.quantity} {self.product.name} en el carrito de {self.cart.user.username}"
    
    def clean(self):
        if self.quantity < 1:
            raise ValidationError("La cantidad debe ser al menos 1")
        if self.quantity > self.product.quantity:
            raise ValidationError("No hay suficiente stock para añadir al carrito")
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Only for new records
            self.current_price = self.product.price
        super().save(*args, **kwargs)
    
    @property
    def subtotal(self):
        return self.quantity * self.current_price