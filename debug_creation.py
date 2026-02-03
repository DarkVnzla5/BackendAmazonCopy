import os
import django
import sys

# Add the backend directory to sys.path
sys.path.append(r'c:\Users\Vuelvan Cara\Desktop\Backend_copiaMercadolibre')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend_copiaMercadolibre.settings')
django.setup()

from api.models import Product, ProductImage
from api.serializers import ProductSerializer
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()

data = {
    "code": "DEBUG_IMG_01",
    "name": "Debug Product",
    "brand": "DebugBrand",
    "category": "DebugCategory",
    "price": 100,
    "quantity": 10,
    "images": ["https://example.com/test-image.jpg"]
}

request = factory.post('/api/products/', data, format='json')

# Simulate the viewset context
class MockContext:
    def __init__(self, request):
        self.request = request
        self.data = request.data # For DRF, usually request.data is parsed, but factory request needs parsing
        
# For factory request, we need to treat it carefully or use standard serializer call
# But simpler: just manually test the logic inside serializer's create method
print("Testing manual creation logic...")

try:
    product = Product.objects.create(
        code="MANUAL_01",
        name="Manual Product",
        brand="Brand",
        category="Cat",
        price=50,
        quantity=5
    )
    print(f"Product created: {product}")
    
    img_url = "https://example.com/manual.jpg"
    img = ProductImage.objects.create(product=product, image=img_url)
    print(f"Image created: {img.image.name}")
    
    # Check if it persists
    print(f"DB count: {ProductImage.objects.filter(product=product).count()}")
    
except Exception as e:
    print(f"Error: {e}")
