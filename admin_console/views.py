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
# admin_console/user_views.py
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import AdminActivity
from .serializers import AdminUserSerializer

User = get_user_model()

class AdminUserListCreateView(generics.ListCreateAPIView):
    """
    List all users or create a new one (admin only)
    """
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AdminUserSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'username', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['date_joined', 'email', 'username', 'last_name']
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active_bool)
        
        # Filter by staff status
        is_staff = self.request.query_params.get('is_staff')
        if is_staff is not None:
            is_staff_bool = is_staff.lower() == 'true'
            queryset = queryset.filter(is_staff=is_staff_bool)
        
        # Filter by role
        role = self.request.query_params.get('role')
        if role:
            if role == 'user':
                queryset = queryset.filter(is_staff=False, is_superuser=False)
            elif role == 'admin':
                queryset = queryset.filter(is_staff=True, is_superuser=False)
            elif role == 'superadmin':
                queryset = queryset.filter(is_superuser=True)
        
        # Search by query parameter
        query = self.request.query_params.get('q')
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query) |
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        # Check if role is provided in request data
        role = self.request.data.get('role')
        
        # Set the is_staff and is_superuser values based on the role
        user_data = {}
        if role:
            if role == 'admin':
                user_data['is_staff'] = True
                user_data['is_superuser'] = False
            elif role == 'superadmin':
                user_data['is_staff'] = True
                user_data['is_superuser'] = True
            else:  # Default to regular user
                user_data['is_staff'] = False
                user_data['is_superuser'] = False
        
        # Create user with updated data
        user = serializer.save(**user_data)
        
        # Log admin activity
        AdminActivity.objects.create(
            user=self.request.user,
            activity_type='user_created',
            description=f'User created: {user.email}',
            ip_address=self.request.META.get('REMOTE_ADDR', '')
        )


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a user (admin only)
    """
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_update(self, serializer):
        # Check if role is provided in request data
        role = self.request.data.get('role')
        
        # Set the is_staff and is_superuser values based on the role
        user_data = {}
        if role:
            if role == 'admin':
                user_data['is_staff'] = True
                user_data['is_superuser'] = False
            elif role == 'superadmin':
                user_data['is_staff'] = True
                user_data['is_superuser'] = True
            elif role == 'user':
                user_data['is_staff'] = False
                user_data['is_superuser'] = False
        
        # Update user with role data if provided
        user = serializer.save(**user_data)
        
        # Log admin activity
        AdminActivity.objects.create(
            user=self.request.user,
            activity_type='user_updated',
            description=f'User updated: {user.email}',
            ip_address=self.request.META.get('REMOTE_ADDR', '')
        )
    
    def perform_destroy(self, instance):
        email = instance.email
        instance.delete()
        
        # Log admin activity
        AdminActivity.objects.create(
            user=self.request.user,
            activity_type='user_deleted',
            description=f'User deleted: {email}',
            ip_address=self.request.META.get('REMOTE_ADDR', '')
        )


class ToggleUserStatusView(APIView):
    """
    Toggle user active status (admin only)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
            user.is_active = not user.is_active
            user.save()
            
            status_str = "activated" if user.is_active else "deactivated"
            
            # Log admin activity
            AdminActivity.objects.create(
                user=request.user,
                activity_type='user_updated',
                description=f'User {status_str}: {user.email}',
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'is_active': user.is_active,
                'message': f'User has been {status_str}'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class ChangeUserRoleView(APIView):
    """
    Change user role (admin only)
    """
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, pk):
        try:
            # Only superusers can assign superadmin role
            if not request.user.is_superuser and request.data.get('role') == 'superadmin':
                return Response(
                    {'error': 'Only superusers can assign superadmin role'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            user = User.objects.get(pk=pk)
            role = request.data.get('role')
            
            if not role or role not in ['user', 'admin', 'superadmin']:
                return Response(
                    {'error': 'Invalid role. Must be one of: user, admin, superadmin'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set permissions based on role
            if role == 'user':
                user.is_staff = False
                user.is_superuser = False
            elif role == 'admin':
                user.is_staff = True
                user.is_superuser = False
            elif role == 'superadmin':
                user.is_staff = True
                user.is_superuser = True
            
            user.save()
            
            # Log admin activity
            AdminActivity.objects.create(
                user=request.user,
                activity_type='user_updated',
                description=f'User role changed to {role}: {user.email}',
                ip_address=request.META.get('REMOTE_ADDR', '')
            )
            
            return Response({
                'success': True,
                'role': role,
                'message': f'User role has been changed to {role}'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )