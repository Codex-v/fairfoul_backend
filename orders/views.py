# orders/views.py
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model
import uuid

from .models import Cart, CartItem, Order, OrderItem, Coupon, OrderEvent
from users.models import Address
from products.models import Product, ProductSize, ProductColor

from .serializers import (
    CartSerializer, CartItemSerializer, CartItemCreateSerializer,
    OrderSerializer, OrderCreateSerializer, OrderItemSerializer,
    CouponSerializer, CouponValidateSerializer, OrderEventSerializer
)
from core.permissions import IsOwnerOrAdmin

User = get_user_model()

class CartView(generics.RetrieveAPIView):
    """
    Retrieve the current user's cart
    """
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart


class CartItemViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for cart items
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return CartItemCreateSerializer
        return CartItemSerializer
    
    def get_queryset(self):
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Return the full cart with the newly added item
        cart = Cart.objects.get(user=request.user)
        cart_serializer = CartSerializer(cart, context={'request': request})
        
        return Response(cart_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """
        Clear all items from the cart
        """
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=True, methods=['patch'])
    def update_quantity(self, request, pk=None):
        """
        Update cart item quantity
        """
        cart_item = self.get_object()
        quantity = request.data.get('quantity', 1)
        
        # Ensure quantity is at least 1
        if quantity < 1:
            return Response(
                {"quantity": "Quantity must be at least 1"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the requested quantity is available
        product_size = cart_item.product.productsize_set.filter(size=cart_item.size).first()
        if product_size and product_size.is_available and product_size.stock_quantity < quantity:
            return Response(
                {"quantity": f"Only {product_size.stock_quantity} items available"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart_item.quantity = quantity
        cart_item.save()
        
        # Return the updated cart
        cart = Cart.objects.get(user=request.user)
        cart_serializer = CartSerializer(cart, context={'request': request})
        
        return Response(cart_serializer.data)


class OrderViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for orders
    """
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    def get_queryset(self):
        # Regular users can only see their own orders
        if self.request.user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=self.request.user)
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Get the user's cart
        try:
            cart = Cart.objects.get(user=request.user)
            if cart.items.count() == 0:
                return Response(
                    {"detail": "Your cart is empty"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Cart.DoesNotExist:
            return Response(
                {"detail": "Your cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get addresses
        shipping_address = get_object_or_404(
            Address, id=serializer.validated_data['shipping_address_id'], user=request.user
        )
        
        billing_address_id = serializer.validated_data.get('billing_address_id')
        if billing_address_id:
            billing_address = get_object_or_404(
                Address, id=billing_address_id, user=request.user
            )
        else:
            # Use shipping address as billing address
            billing_address = shipping_address
        
        # Calculate order totals
        subtotal = cart.subtotal
        shipping_cost = 0  # Free shipping for now (can be calculated based on rules)
        tax = 0  # Tax calculation would go here
        discount = 0
        
        # Apply coupon if provided
        coupon = serializer.validated_data.get('coupon')
        if coupon:
            if coupon.discount_amount > 0:
                discount = min(coupon.discount_amount, subtotal)
            elif coupon.discount_percentage > 0:
                discount = (subtotal * coupon.discount_percentage / 100)
            
            # Update coupon usage count
            coupon.times_used += 1
            coupon.save()
        
        total = subtotal + shipping_cost + tax - discount
        
        # Generate order number
        order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        # Create the order
        order = Order.objects.create(
            order_number=order_number,
            user=request.user,
            shipping_address=shipping_address,
            billing_address=billing_address,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            discount=discount,
            total=total,
            customer_notes=serializer.validated_data.get('customer_notes', ''),
            order_status='pending',
            payment_status='pending'
        )
        
        # Create order items from cart items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_sku=cart_item.product.sku or '',
                color=cart_item.color,
                color_name=cart_item.color.color.name if cart_item.color else '',
                size=cart_item.size,
                size_name=cart_item.size.name,
                price=cart_item.product.price,
                quantity=cart_item.quantity
            )
        
        # Log the order creation event
        OrderEvent.objects.create(
            order=order,
            event_type='status_change',
            description='Order created',
            created_by=request.user
        )
        
        # Clear the cart
        cart.items.all().delete()
        
        # Return the created order
        order_serializer = OrderSerializer(order, context={'request': request})
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Cancel an order if it's not shipped yet
        """
        order = self.get_object()
        
        # Check if order can be cancelled
        if order.order_status in ['shipped', 'delivered']:
            return Response(
                {"detail": "Cannot cancel an order that has been shipped or delivered"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.order_status = 'cancelled'
        order.save()
        
        # Log the event
        OrderEvent.objects.create(
            order=order,
            event_type='status_change',
            description=f'Order cancelled. Reason: {request.data.get("reason", "Not provided")}',
            created_by=request.user
        )
        
        return Response({"detail": "Order cancelled successfully"})
    
    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """
        Add a note to an order
        """
        order = self.get_object()
        note = request.data.get('note', '')
        
        if not note:
            return Response(
                {"note": "Note cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create an event for the note
        OrderEvent.objects.create(
            order=order,
            event_type='note_added',
            description=note,
            created_by=request.user
        )
        
        return Response({"detail": "Note added successfully"})


class AdminOrderViewSet(viewsets.ModelViewSet):
    """
    Admin-only order management
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update order status (admin only)
        """
        order = self.get_object()
        status_value = request.data.get('status')
        
        if not status_value or status_value not in dict(Order.ORDER_STATUS_CHOICES):
            return Response(
                {"status": "Invalid status value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the order status
        old_status = order.order_status
        order.order_status = status_value
        order.save()
        
        # Log the status change
        OrderEvent.objects.create(
            order=order,
            event_type='status_change',
            description=f'Order status changed from {old_status} to {status_value}',
            created_by=request.user
        )
        
        # If marked as shipped, update tracking info if provided
        if status_value == 'shipped':
            tracking_number = request.data.get('tracking_number')
            shipping_carrier = request.data.get('shipping_carrier')
            
            if tracking_number:
                order.tracking_number = tracking_number
                order.shipping_carrier = shipping_carrier or ''
                order.save()
                
                # Log tracking update
                OrderEvent.objects.create(
                    order=order,
                    event_type='tracking_updated',
                    description=f'Tracking information added: {shipping_carrier} - {tracking_number}',
                    created_by=request.user
                )
        
        return Response({"detail": "Order status updated successfully"})
    
    @action(detail=True, methods=['post'])
    def update_payment(self, request, pk=None):
        """
        Update payment status (admin only)
        """
        order = self.get_object()
        payment_status = request.data.get('payment_status')
        
        if not payment_status or payment_status not in dict(Order.PAYMENT_STATUS_CHOICES):
            return Response(
                {"payment_status": "Invalid payment status value"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the payment status
        old_status = order.payment_status
        order.payment_status = payment_status
        order.save()
        
        # Log the payment status change
        OrderEvent.objects.create(
            order=order,
            event_type='payment_update',
            description=f'Payment status changed from {old_status} to {payment_status}',
            created_by=request.user
        )
        
        return Response({"detail": "Payment status updated successfully"})


class CouponViewSet(viewsets.ModelViewSet):
    """
    CRUD operations for coupons (admin only)
    """
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [permissions.IsAdminUser]


class ValidateCouponView(generics.GenericAPIView):
    """
    Validate a coupon code
    """
    serializer_class = CouponValidateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        code = serializer.validated_data['code']
        try:
            coupon = Coupon.objects.get(code=code)
            
            # Check if coupon is valid
            if not coupon.is_valid:
                return Response(
                    {"detail": "This coupon code is not valid or has expired."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get cart value to check minimum order amount
            try:
                cart = Cart.objects.get(user=request.user)
                subtotal = cart.subtotal
                
                if subtotal < coupon.minimum_order_amount:
                    return Response({
                        "detail": f"This coupon requires a minimum order of ${coupon.minimum_order_amount}."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Calculate discount
                discount = 0
                if coupon.discount_amount > 0:
                    discount = min(coupon.discount_amount, subtotal)
                elif coupon.discount_percentage > 0:
                    discount = (subtotal * coupon.discount_percentage / 100)
                
                return Response({
                    "coupon": CouponSerializer(coupon).data,
                    "discount": discount,
                    "cart_total": subtotal,
                    "final_total": subtotal - discount
                })
                
            except Cart.DoesNotExist:
                return Response({
                    "detail": "Your cart is empty."
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Coupon.DoesNotExist:
            return Response(
                {"detail": "Invalid coupon code."},
                status=status.HTTP_404_NOT_FOUND
            )