# admin_console/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AdminActivityViewSet, 
    DashboardMetricsView,
    AdminDashboardView,
    AdminReportingView
)
# from .admin_user_views import AdminUserViewSet
from .auth_views import AdminLoginView, AdminLogoutView, AdminVerifyTokenView

# Router for admin activities
router = DefaultRouter()
router.register(r'activities', AdminActivityViewSet, basename='admin-activity')
# router.register(r'users', AdminUserViewSet, basename='admin-user')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Admin authentication endpoints
    path('auth/login/', AdminLoginView.as_view(), name='admin_login'),
    path('auth/logout/', AdminLogoutView.as_view(), name='admin_logout'),
    path('auth/verify/', AdminVerifyTokenView.as_view(), name='admin_verify'),
    
    # Dashboard endpoints
    path('metrics/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('reporting/', AdminReportingView.as_view(), name='admin-reporting'),
]