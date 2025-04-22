# admin_console/views.py
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from django.db import transaction

from .models import AdminActivity, DashboardMetrics
from .serializers import (
    AdminActivitySerializer, 
    AdminDashboardSerializer, 
    DashboardMetricsSerializer
)
from users.models import User
from products.models import Product
from orders.models import Order, Coupon
from core.permissions import IsAdminUserOrReadOnly

from admin_console import models

class AdminActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for admin activities
    """
    queryset = AdminActivity.objects.all()
    serializer_class = AdminActivitySerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = AdminActivity.objects.all()
        
        # Filter by activity type
        activity_type = self.request.query_params.get('activity_type')
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date and end_date:
            queryset = queryset.filter(
                created_at__range=[start_date, end_date]
            )
        
        return queryset.order_by('-created_at')


class DashboardMetricsView(generics.RetrieveAPIView):
    """
    Retrieve dashboard metrics
    """
    serializer_class = DashboardMetricsSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_object(self):
        # Always create or update metrics
        metrics, created = DashboardMetrics.objects.get_or_create(pk=1)
        
        # Update metrics
        metrics.total_users = User.objects.count()
        metrics.total_products = Product.objects.count()
        metrics.total_orders = Order.objects.count()
        
        # Calculate total revenue (from completed orders)
        metrics.total_revenue = Order.objects.filter(
            order_status='delivered'
        ).aggregate(total=models.Sum('total'))['total'] or 0
        
        metrics.save()
        return metrics


class AdminDashboardView(APIView):
    """
    Comprehensive admin dashboard view
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """
        Get comprehensive dashboard data
        """
        # Use the serializer to generate dashboard data
        serializer = AdminDashboardSerializer(data={})
        
        # This will trigger the to_representation method which calculates metrics
        return Response(serializer.to_representation(None))


class AdminReportingView(APIView):
    """
    Advanced reporting and analytics
    """
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """
        Generate various reports
        """
        report_type = request.query_params.get('type', 'sales')
        
        if report_type == 'sales':
            # Sales report by month
            sales_report = Order.objects.filter(
                order_status='delivered'
            ).annotate(
                month=TruncMonth('created_at')
            ).values('month').annotate(
                total_sales=Sum('total'),
                total_orders=Count('id')
            ).order_by('month')
            
            return Response(sales_report)
        
        elif report_type == 'product_performance':
            # Top-performing products
            product_performance = Product.objects.annotate(
                total_sales=Sum('orderitem__price', filter=Q(orderitem__order__order_status='delivered')),
                total_orders=Count('orderitem', filter=Q(orderitem__order__order_status='delivered'))
            ).order_by('-total_sales')[:10]
            
            serializer = ProductPerformanceSerializer(product_performance, many=True)
            return Response(serializer.data)
        
        elif report_type == 'user_activity':
            # User activity report
            user_activity = User.objects.annotate(
                total_orders=Count('orders', filter=Q(orders__order_status='delivered')),
                total_spent=Sum('orders__total', filter=Q(orders__order_status='delivered'))
            ).order_by('-total_spent')[:50]
            
            serializer = UserActivitySerializer(user_activity, many=True)
            return Response(serializer.data)
        
        else:
            return Response(
                {"detail": "Invalid report type"}, 
                status=status.HTTP_400_BAD_REQUEST
            )