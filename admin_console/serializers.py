# admin_console/serializers.py
from rest_framework import serializers
from .models import AdminActivity, DashboardMetrics
from users.models import User
from products.models import Product
from orders.models import Order, Coupon

class AdminActivitySerializer(serializers.ModelSerializer):
    """
    Serializer for admin activities
    """
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = AdminActivity
        fields = (
            'id', 'user', 'user_email', 'activity_type', 
            'description', 'ip_address', 'created_at'
        )
        read_only_fields = ('created_at',)


class DashboardMetricsSerializer(serializers.ModelSerializer):
    """
    Serializer for dashboard metrics
    """
    class Meta:
        model = DashboardMetrics
        fields = '__all__'
        read_only_fields = fields


class AdminDashboardSerializer(serializers.Serializer):
    """
    Comprehensive dashboard serializer with various metrics
    """
    # User metrics
    total_users = serializers.IntegerField()
    total_active_users = serializers.IntegerField()
    new_users_this_month = serializers.IntegerField()
    
    # Product metrics
    total_products = serializers.IntegerField()
    total_active_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    
    # Order metrics
    total_orders = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    monthly_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    
    # Sales by category
    top_categories = serializers.ListField(
        child=serializers.DictField()
    )
    
    # Recent activities
    recent_activities = AdminActivitySerializer(many=True)
    
    def to_representation(self, instance):
        from django.utils import timezone
        from django.db.models import Sum, Count, Q
        from django.db.models.functions import TruncMonth
        
        # User metrics
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users_this_month = User.objects.filter(
            date_joined__month=timezone.now().month,
            date_joined__year=timezone.now().year
        ).count()
        
        # Product metrics
        total_products = Product.objects.count()
        active_products = Product.objects.filter(is_active=True).count()
        low_stock_products = Product.objects.filter(stock_quantity__lte=5).count()
        
        # Order metrics
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(order_status='pending').count()
        completed_orders = Order.objects.filter(order_status='delivered').count()
        
        # Monthly revenue
        current_month = timezone.now().month
        current_year = timezone.now().year
        monthly_revenue = Order.objects.filter(
            created_at__month=current_month,
            created_at__year=current_year,
            order_status='delivered'
        ).aggregate(total_revenue=Sum('total'))['total_revenue'] or 0
        
        # Top categories by sales
        from django.db.models import F
        from products.models import Category
        top_categories = Order.objects.filter(
            order_status='delivered'
        ).values(
            category_name=F('items__product__category__name')
        ).annotate(
            total_sales=Sum('items__price')
        ).order_by('-total_sales')[:5]
        
        # Recent admin activities
        recent_activities = AdminActivity.objects.order_by('-created_at')[:10]
        
        return {
            'total_users': total_users,
            'total_active_users': active_users,
            'new_users_this_month': new_users_this_month,
            'total_products': total_products,
            'total_active_products': active_products,
            'low_stock_products': low_stock_products,
            'total_orders': total_orders,
            'pending_orders': pending_orders,
            'completed_orders': completed_orders,
            'monthly_revenue': monthly_revenue,
            'top_categories': list(top_categories),
            'recent_activities': AdminActivitySerializer(recent_activities, many=True).data
        }
    


# admin_console/serializers.py - Update this part

from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class AdminUserSerializer(serializers.ModelSerializer):
    """
    Serializer for admin user management
    """
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=False)
    orders_count = serializers.SerializerMethodField()
    last_login_display = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 
            'is_active', 'is_staff', 'is_superuser', 'phone_number',
            'date_joined', 'last_login', 'last_login_display',
            'profile_picture', 'is_email_verified', 'password',
            'confirm_password', 'orders_count', 'role'
        )
        read_only_fields = ('date_joined', 'last_login', 'orders_count', 'role')

    def get_orders_count(self, obj):
        """
        Get the number of orders placed by the user
        """
        return obj.orders.count() if hasattr(obj, 'orders') else 0
    
    def get_last_login_display(self, obj):
        """
        Format last login date for display
        """
        if obj.last_login:
            return obj.last_login.strftime("%Y-%m-%d %H:%M:%S")
        return "Never"
    
    def get_role(self, obj):
        """
        Get the user's role
        """
        if obj.is_superuser:
            return "superadmin"
        elif obj.is_staff:
            return "admin"
        return "user"
    
    def validate(self, data):
        """
        Validate password confirmation matches
        """
        if 'password' in data and 'confirm_password' in data:
            if data['password'] != data['confirm_password']:
                raise serializers.ValidationError({
                    "password": "Password fields didn't match."
                })
        
        # Remove confirm_password from the data
        if 'confirm_password' in data:
            data.pop('confirm_password')
            
        return data
    
    def create(self, validated_data):
        """
        Create and return a new user with encrypted password
        """
        password = validated_data.pop('password', None)
        
        # Instead of getting role from context, get it from the view
        # and add it as is_staff and is_superuser in validated_data
        
        user = User.objects.create(
            **validated_data
        )
        
        if password:
            user.set_password(password)
            user.save()
            
        return user
    
    def update(self, instance, validated_data):
        """
        Update user details, handling password updates separately
        """
        password = validated_data.pop('password', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if password:
            instance.set_password(password)
            
        instance.save()
        return instance