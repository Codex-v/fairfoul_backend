# orders/serializers.py
from rest_framework import serializers
from .models import Cart, CartItem, Order, OrderItem, Coupon, OrderEvent
from products.serializers import ProductListSerializer
from users.serializers import AddressSerializer

class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for cart items
    """
    product_details = ProductListSerializer(source='product', read_only=True)
    total_price = serializers.SerializerMethodField()
    color_name = serializers.CharField(source='color.color.name', read_only=True)
    color_hex = serializers.CharField(source='color.color.hex_value', read_only=True)
    size_name = serializers.CharField(source='size.name', read_only=True)
    
    class Meta:
        model = CartItem
        fields = (
            'id', 'product', 'product_details', 'color', 'color_name', 
            'color_hex', 'size', 'size_name', 'quantity', 'total_price',
            'created_at', 'updated_at'
        )
        read_only_fields = ('cart', 'created_at', 'updated_at')
    
    def get_total_price(self, obj):
        return obj.total_price


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for shopping cart
    """
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ('id', 'user', 'items', 'total_items', 'subtotal', 'created_at', 'updated_at')
        read_only_fields = ('user', 'created_at', 'updated_at')


class CartItemCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating cart items
    """
    class Meta:
        model = CartItem
        fields = ('id', 'product', 'color', 'size', 'quantity')
    
    def validate(self, data):
        # Check if the product is in stock
        product = data['product']
        if not product.in_stock:
            raise serializers.ValidationError("This product is currently out of stock.")
        
        # Check if the size is available for this product
        try:
            product_size = product.productsize_set.get(size=data['size'])
            if not product_size.is_available or product_size.stock_quantity < data['quantity']:
                raise serializers.ValidationError("The selected size is not available in the requested quantity.")
        except:
            raise serializers.ValidationError("The selected size is not available for this product.")
        
        # Check if the color is valid for this product
        if data.get('color') and not product.colors.filter(id=data['color'].id).exists():
            raise serializers.ValidationError("The selected color is not available for this product.")
        
        return data
    
    def create(self, validated_data):
        cart = Cart.objects.get_or_create(user=self.context['request'].user)[0]
        
        # Check if this item already exists in the cart
        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product=validated_data['product'],
                color=validated_data.get('color'),
                size=validated_data['size']
            )
            # Update quantity if it exists
            cart_item.quantity += validated_data['quantity']
            cart_item.save()
            return cart_item
        except CartItem.DoesNotExist:
            # Create new cart item
            return CartItem.objects.create(cart=cart, **validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for order items
    """
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = (
            'id', 'product', 'product_name', 'product_sku',
            'color', 'color_name', 'size', 'size_name',
            'price', 'quantity', 'total_price'
        )
        read_only_fields = ('product_name', 'product_sku', 'color_name', 'size_name')


class OrderEventSerializer(serializers.ModelSerializer):
    """
    Serializer for order events
    """
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = OrderEvent
        fields = ('id', 'event_type', 'description', 'created_by', 'created_by_name', 'created_at')
        read_only_fields = ('created_at',)
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for orders
    """
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address_details = AddressSerializer(source='shipping_address', read_only=True)
    billing_address_details = AddressSerializer(source='billing_address', read_only=True)
    events = OrderEventSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'user', 'shipping_address', 'shipping_address_details',
            'billing_address', 'billing_address_details', 'subtotal', 'shipping_cost',
            'tax', 'discount', 'total', 'order_status', 'payment_status',
            'customer_notes', 'tracking_number', 'shipping_carrier',
            'items', 'events', 'created_at', 'updated_at'
        )
        read_only_fields = ('order_number', 'created_at', 'updated_at')


class OrderCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating orders
    """
    shipping_address_id = serializers.IntegerField(write_only=True)
    billing_address_id = serializers.IntegerField(write_only=True, required=False)
    coupon_code = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = Order
        fields = (
            'shipping_address_id', 'billing_address_id', 'customer_notes',
            'coupon_code'
        )
    
    def validate(self, data):
        # Validate shipping address
        user = self.context['request'].user
        try:
            shipping_address = user.addresses.get(id=data['shipping_address_id'])
        except:
            raise serializers.ValidationError({"shipping_address_id": "Invalid shipping address."})
        
        # Validate billing address if provided
        if 'billing_address_id' in data:
            try:
                billing_address = user.addresses.get(id=data['billing_address_id'])
            except:
                raise serializers.ValidationError({"billing_address_id": "Invalid billing address."})
        
        # Check if cart has items
        try:
            cart = user.cart
            if cart.items.count() == 0:
                raise serializers.ValidationError({"non_field_errors": "Your cart is empty."})
        except:
            raise serializers.ValidationError({"non_field_errors": "Your cart is empty."})
        
        # Validate coupon if provided
        if data.get('coupon_code'):
            try:
                coupon = Coupon.objects.get(code=data['coupon_code'])
                if not coupon.is_valid:
                    raise serializers.ValidationError({"coupon_code": "This coupon is not valid."})
                
                # Check minimum order amount
                if cart.subtotal < coupon.minimum_order_amount:
                    raise serializers.ValidationError({
                        "coupon_code": f"This coupon requires a minimum order of ${coupon.minimum_order_amount}."
                    })
                
                data['coupon'] = coupon
            except Coupon.DoesNotExist:
                raise serializers.ValidationError({"coupon_code": "Invalid coupon code."})
        
        return data


class CouponSerializer(serializers.ModelSerializer):
    """
    Serializer for coupons
    """
    class Meta:
        model = Coupon
        fields = (
            'id', 'code', 'description', 'discount_amount', 'discount_percentage',
            'minimum_order_amount', 'is_active', 'valid_from', 'valid_to',
            'usage_limit', 'times_used', 'is_valid'
        )
        read_only_fields = ('times_used', 'is_valid')


class CouponValidateSerializer(serializers.Serializer):
    """
    Serializer for validating coupon codes
    """
    code = serializers.CharField()
    
    def validate_code(self, value):
        try:
            coupon = Coupon.objects.get(code=value)
            if not coupon.is_valid:
                raise serializers.ValidationError("This coupon code is not valid.")
            return value
        except Coupon.DoesNotExist:
            raise serializers.ValidationError("Invalid coupon code.")