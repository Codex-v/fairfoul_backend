# admin_console/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from products.models import Product
from orders.models import Order, Coupon
from .models import AdminActivity

User = get_user_model()

def log_admin_activity(user, activity_type, description, ip_address=None):
    """
    Helper function to log admin activities
    """
    if user and user.is_staff:
        AdminActivity.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address
        )

# User activity signals
@receiver(post_save, sender=User)
def log_user_creation(sender, instance, created, **kwargs):
    """
    Log user creation/update activities
    """
    if instance.is_staff:
        if created:
            log_admin_activity(
                instance, 
                'user_created', 
                f'User account created: {instance.email}'
            )
        else:
            log_admin_activity(
                instance, 
                'user_updated', 
                f'User account updated: {instance.email}'
            )

@receiver(post_delete, sender=User)
def log_user_deletion(sender, instance, **kwargs):
    """
    Log user deletion activities
    """
    if instance.is_staff:
        log_admin_activity(
            instance, 
            'user_deleted', 
            f'User account deleted: {instance.email}'
        )

# Product activity signals
@receiver(post_save, sender=Product)
def log_product_activity(sender, instance, created, **kwargs):
    """
    Log product creation/update activities
    """
    if created:
        log_admin_activity(
            kwargs.get('user', None), 
            'product_created', 
            f'Product created: {instance.name}'
        )
    else:
        log_admin_activity(
            kwargs.get('user', None), 
            'product_updated', 
            f'Product updated: {instance.name}'
        )

@receiver(post_delete, sender=Product)
def log_product_deletion(sender, instance, **kwargs):
    """
    Log product deletion activities
    """
    log_admin_activity(
        kwargs.get('user', None), 
        'product_deleted', 
        f'Product deleted: {instance.name}'
    )

# Order status change logging
@receiver(post_save, sender=Order)
def log_order_status_change(sender, instance, created, **kwargs):
    """
    Log order status updates
    """
    if not created and instance.order_status:
        log_admin_activity(
            kwargs.get('user', None), 
            'order_status_updated', 
            f'Order {instance.order_number} status changed to {instance.order_status}'
        )

# Coupon activity signals
@receiver(post_save, sender=Coupon)
def log_coupon_activity(sender, instance, created, **kwargs):
    """
    Log coupon creation/update activities
    """
    if created:
        log_admin_activity(
            kwargs.get('user', None), 
            'coupon_created', 
            f'Coupon created: {instance.code}'
        )
    else:
        log_admin_activity(
            kwargs.get('user', None), 
            'coupon_updated', 
            f'Coupon updated: {instance.code}'
        )