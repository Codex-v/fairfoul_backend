# orders/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CartView, CartItemViewSet, OrderViewSet, 
    AdminOrderViewSet, CouponViewSet, ValidateCouponView
)

# Regular user routes
router = DefaultRouter()
router.register(r'cart/items', CartItemViewSet, basename='cart-item')
router.register(r'orders', OrderViewSet, basename='order')

# Admin-only routes
admin_router = DefaultRouter()
admin_router.register(r'orders', AdminOrderViewSet, basename='admin-order')
admin_router.register(r'coupons', CouponViewSet, basename='coupon')

urlpatterns = [
    # Cart endpoints
    path('cart/', CartView.as_view(), name='cart'),
    
    # Include router URLs
    path('', include(router.urls)),
    
    # Coupon validation
    path('coupon/validate/', ValidateCouponView.as_view(), name='validate-coupon'),
    
    # Admin endpoints
    path('admin/', include(admin_router.urls)),
]