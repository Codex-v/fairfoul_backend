# admin_console/views.py
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.db.models.functions import TruncMonth


from .models import AdminActivity, DashboardMetrics
from .serializers import (
    AdminActivitySerializer, 
    AdminDashboardSerializer, 
    DashboardMetricsSerializer
)
from users.models import User
from products.models import Product
from orders.models import Order
from core.permissions import IsAdminUserOrReadOnly
from products.serializers import ProductListSerializer

class LowStockProductsView(generics.ListAPIView):
    """
    Admin view for products with low stock
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """
        Return products with low stock, filtered by various parameters
        """
        # Default threshold value for what's considered "low stock"
        threshold = int(self.request.query_params.get('threshold', 5))
        
        # Build the base queryset for low stock items
        queryset = Product.objects.filter(
            Q(stock_quantity__lte=threshold) | 
            Q(productsize__stock_quantity__lte=threshold)
        ).distinct()
        
        # Filter by stock status if specified
        in_stock = self.request.query_params.get('in_stock')
        if in_stock is not None:
            in_stock_bool = in_stock.lower() == 'true'
            queryset = queryset.filter(in_stock=in_stock_bool)
        
        # Filter by category if specified
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Return paginated, ordered results
        return queryset.order_by('stock_quantity')



class AdminActivityListCreateView(generics.ListCreateAPIView):
    """
    List all admin activities or create a new one
    """
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


class AdminActivityDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an admin activity
    """
    queryset = AdminActivity.objects.all()
    serializer_class = AdminActivitySerializer
    permission_classes = [permissions.IsAdminUser]


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
        ).aggregate(total=Sum('total'))['total'] or 0
        
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
            
            from products.serializers import ProductListSerializer
            serializer = ProductListSerializer(product_performance, many=True, context={'request': request})
            return Response(serializer.data)
        
        elif report_type == 'user_activity':
            # User activity report
            user_activity = User.objects.annotate(
                total_orders=Count('orders', filter=Q(orders__order_status='delivered')),
                total_spent=Sum('orders__total', filter=Q(orders__order_status='delivered'))
            ).order_by('-total_spent')[:50]
            
            from users.serializers import UserProfileSerializer
            serializer = UserProfileSerializer(user_activity, many=True)
            return Response(serializer.data)
        
        else:
            return Response(
                {"detail": "Invalid report type"}, 
                status=status.HTTP_400_BAD_REQUEST
            )