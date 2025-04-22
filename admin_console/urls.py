# admin_console/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AdminActivityViewSet, 
    DashboardMetricsView,
    AdminDashboardView,
    AdminReportingView
)

# Router for admin activities
router = DefaultRouter()
router.register(r'activities', AdminActivityViewSet, basename='admin-activity')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Dashboard endpoints
    path('metrics/', DashboardMetricsView.as_view(), name='dashboard-metrics'),
    path('dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('reporting/', AdminReportingView.as_view(), name='admin-reporting'),
]