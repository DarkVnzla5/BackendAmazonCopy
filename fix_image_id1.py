import os
import django
import sys

sys.path.append(r'c:\Users\Vuelvan Cara\Desktop\Backend_copiaMercadolibre')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend_copiaMercadolibre.settings')
django.setup()

from api.models import Product, ProductImage

try:
    p = Product.objects.get(id=1)
    print(f"Updating {p.name}...")
    
    # Clear existing images
    p.images.all().delete()
    
    # Add valid placeholder
    url = "https://via.placeholder.com/150"
    ProductImage.objects.create(product=p, image=url)
    
    print(f"Added image {url} to {p.name}")
    print(f"Current images: {[i.image.name for i in p.images.all()]}")

except Product.DoesNotExist:
    print("Product ID 1 not found")
except Exception as e:
    print(f"Error: {e}")
