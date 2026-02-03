import os
import django
import sys

# Add the backend directory to sys.path
sys.path.append(r'c:\Users\Vuelvan Cara\Desktop\Backend_copiaMercadolibre')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Backend_copiaMercadolibre.settings')
django.setup()

from api.models import ProductImage

print(f"Total Images: {ProductImage.objects.count()}")
for img in ProductImage.objects.all():
    print(f"ID: {img.id}, Name: '{img.image.name}', Product: {img.product.name}")
