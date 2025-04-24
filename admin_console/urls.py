# admin_console/urls.py
from django.urls import path, include

from .views import (
    AdminActivityListCreateView,
    AdminActivityDetailView,
    DashboardMetricsView,
    AdminDashboardView,
    AdminReportingView,
    LowStockProductsView  # Add the new view
)
from .auth_views import AdminLoginView, AdminLogoutView, AdminVerifyTokenView

urlpatterns = [
    # Admin activity endpoints
    path('activities/', AdminActivityListCreateView.as_view(), name='admin-activity-list'),
    path('activities/<int:pk>/', AdminActivityDetailView.as_view(), name='admin-activity-detail'),
    
    # Admin authentication endpoints
    path('auth/login/', AdminLoginView.as_view(), name='admin_login'),
    path('auth/logout/', AdminLogoutView.as_view(), name='admin_logout'),
    path('auth/verify/', AdminVerifyTokenView.as_view(), name='admin_verify'),
    
    # Dashboard endpoints
    path('metrics/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('reporting/', AdminReportingView.as_view(), name='admin-reporting'),
    
    # Product management endpoints
    path('products/', LowStockProductsView.as_view(), name='low-stock-products'),
]