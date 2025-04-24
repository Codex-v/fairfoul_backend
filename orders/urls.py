# orders/urls.py
from django.urls import path
from .views import (
    CartView, CartItemListCreateView, CartItemDetailView, CartClearView, CartItemQuantityUpdateView,
    OrderListCreateView, OrderDetailView, OrderCancelView, OrderNoteAddView,
    AdminOrderListView, AdminOrderDetailView, AdminOrderStatusUpdateView, AdminOrderPaymentUpdateView,
    CouponListCreateView, CouponDetailView, ValidateCouponView
)

urlpatterns = [
    # Cart endpoints
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/items/', CartItemListCreateView.as_view(), name='cart-item-list'),
    path('cart/items/<int:pk>/', CartItemDetailView.as_view(), name='cart-item-detail'),
    path('cart/clear/', CartClearView.as_view(), name='cart-clear'),
    path('cart/items/<int:pk>/update-quantity/', CartItemQuantityUpdateView.as_view(), name='cart-item-quantity'),
    # path('cart/items/<int:pk>/update-quantity/', CartItemQuantityUpdateView.as_view(), name='cart-item-quantity'),
    path('cart/items/<int:pk>/update_quantity/', CartItemQuantityUpdateView.as_view(), name='cart-item-quantity'),
    # Order endpoints
    path('orders/', OrderListCreateView.as_view(), name='order-list'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/cancel/', OrderCancelView.as_view(), name='order-cancel'),
    path('orders/<int:pk>/add-note/', OrderNoteAddView.as_view(), name='order-add-note'),
    
    # Coupon validation
    path('coupon/validate/', ValidateCouponView.as_view(), name='validate-coupon'),
    
    # Admin endpoints
    path('admin/orders/', AdminOrderListView.as_view(), name='admin-order-list'),
    path('admin/orders/<int:pk>/', AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/orders/<int:pk>/update-status/', AdminOrderStatusUpdateView.as_view(), name='admin-order-status'),
    path('admin/orders/<int:pk>/update-payment/', AdminOrderPaymentUpdateView.as_view(), name='admin-order-payment'),
    path('admin/coupons/', CouponListCreateView.as_view(), name='coupon-list'),
    path('admin/coupons/<int:pk>/', CouponDetailView.as_view(), name='coupon-detail'),
]