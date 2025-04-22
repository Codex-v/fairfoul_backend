# orders/models.py
from django.db import models
import uuid
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from core.models import TimestampedModel

User = get_user_model()

class Cart(TimestampedModel):
    """
    Shopping cart model
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    
    def __str__(self):
        return f"Cart for {self.user.email}"
    
    @property
    def total_items(self):
        return self.items.count()
    
    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())


class CartItem(TimestampedModel):
    """
    Shopping cart item model
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    color = models.ForeignKey('products.ProductColor', on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey('products.Size', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    
    class Meta:
        unique_together = ('cart', 'product', 'color', 'size')
    
    def __str__(self):
        return f"{self.quantity} x {self.product.name} ({self.size.name})"
    
    @property
    def total_price(self):
        return self.product.price * self.quantity


class Order(TimestampedModel):
    """
    Order model
    """
    ORDER_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='orders')
    
    # Address information
    shipping_address = models.ForeignKey('users.Address', on_delete=models.SET_NULL, null=True, related_name='shipping_orders')
    billing_address = models.ForeignKey('users.Address', on_delete=models.SET_NULL, null=True, related_name='billing_orders')
    
    # Financial details
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Status tracking
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Optional user notes
    customer_notes = models.TextField(blank=True)
    
    # Tracking information
    tracking_number = models.CharField(max_length=100, blank=True)
    shipping_carrier = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.order_number
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate a unique order number
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        # Generate an order number based on timestamp and random string
        prefix = 'ORD'
        unique_id = uuid.uuid4().hex[:8].upper()
        return f"{prefix}-{unique_id}"


class OrderItem(TimestampedModel):
    """
    Order item model
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True)
    # We store product details in case the product is deleted later
    product_name = models.CharField(max_length=255)
    product_sku = models.CharField(max_length=100, blank=True)
    color = models.ForeignKey('products.ProductColor', on_delete=models.SET_NULL, null=True, blank=True)
    color_name = models.CharField(max_length=50, blank=True)
    size = models.ForeignKey('products.Size', on_delete=models.SET_NULL, null=True)
    size_name = models.CharField(max_length=10)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f"{self.quantity} x {self.product_name} ({self.size_name})"
    
    @property
    def total_price(self):
        return self.price * self.quantity
    
    def save(self, *args, **kwargs):
        # Store product details in case product is deleted
        if self.product and not self.product_name:
            self.product_name = self.product.name
            self.product_sku = self.product.sku or ''
        
        if self.color and not self.color_name:
            self.color_name = self.color.color.name
        
        if self.size and not self.size_name:
            self.size_name = self.size.name
            
        super().save(*args, **kwargs)


class Coupon(TimestampedModel):
    """
    Coupon code model
    """
    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=255, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percentage = models.PositiveIntegerField(default=0)
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=0)  # 0 means unlimited
    times_used = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return self.code
    
    @property
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if now < self.valid_from or now > self.valid_to:
            return False
        
        if self.usage_limit > 0 and self.times_used >= self.usage_limit:
            return False
        
        return True


class OrderEvent(TimestampedModel):
    """
    Event log for order status changes
    """
    EVENT_TYPE_CHOICES = [
        ('status_change', 'Status Change'),
        ('payment_update', 'Payment Update'),
        ('note_added', 'Note Added'),
        ('tracking_updated', 'Tracking Updated'),
    ]
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.event_type}"