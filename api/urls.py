# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static
from .views import ProductViewSet, OrderViewSet, UserViewSet, CartViewSet, CartItemViewSet, login_view, dashboard_view

router = DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'users', UserViewSet)
router.register(r'carts', CartViewSet)
router.register(r'cartitems', CartItemViewSet)

from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('', include(router.urls)),
    path('login/', login_view, name='login'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('signup/', UserViewSet.as_view({'post': 'create'}), name='signup'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)