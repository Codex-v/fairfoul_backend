# products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ColorViewSet, SizeViewSet, ProductViewSet,
    ProductImageViewSet, ProductSizeViewSet, ProductColorViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'colors', ColorViewSet, basename='color')
router.register(r'sizes', SizeViewSet, basename='size')
router.register(r'', ProductViewSet, basename='product')

# Admin-only routes
admin_router = DefaultRouter()
admin_router.register(r'images', ProductImageViewSet, basename='product-image')
admin_router.register(r'product-sizes', ProductSizeViewSet, basename='product-size')
admin_router.register(r'product-colors', ProductColorViewSet, basename='product-color')

urlpatterns = [
    # Public product APIs
    path('', include(router.urls)),
    
    # Admin product management APIs
    path('admin/', include(admin_router.urls)),
]