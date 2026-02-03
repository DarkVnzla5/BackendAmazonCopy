from django.contrib import admin
from .models import Product, ProductImage, Order, User, Cart, CartItem

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    list_display = ('code','name', 'price', 'brand','category','quantity','updated_at','created_at')
    search_fields = ('name','code')
    list_filter = ('created_at','name','category','brand')
    ordering = ('-created_at',)
    inlines = [ProductImageInline]
    
class OrderAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'total', 'date')
    search_fields = ('product',)
    list_filter = ( 'created_at','product__name')
    ordering = ('-created_at',)

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# ...

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('role', 'is_staff', 'is_active', 'created_at')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'date_birth')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Fields', {'fields': ('role', 'date_birth', 'email')}),
    )
    
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username',)
    ordering = ('-created_at',)
    
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    search_fields = ('cart__user__username', 'product__name')
    ordering = ('-cart__created_at', '-cart__updated_at')

admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
admin.site.register(ProductImage)

# Register your models here.
