from django.contrib import admin
from .models import AdminActivity, DashboardMetrics

@admin.register(AdminActivity)
class AdminActivityAdmin(admin.ModelAdmin):
    """
    Admin configuration for AdminActivity model
    """
    list_display = ('user', 'activity_type', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__email', 'description')
    readonly_fields = ('user', 'activity_type', 'description', 'ip_address', 'created_at')

@admin.register(DashboardMetrics)
class DashboardMetricsAdmin(admin.ModelAdmin):
    """
    Admin configuration for DashboardMetrics model
    """
    list_display = ('total_users', 'total_products', 'total_orders', 'total_revenue', 'last_updated')
    readonly_fields = ('last_updated',)