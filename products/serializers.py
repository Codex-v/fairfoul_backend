# products/serializers.py - Update these serializers to match frontend expectations

from rest_framework import serializers
from .models import (
    Category, Color, Size, Product, ProductSize, 
    ProductColor, ProductImage, ProductHighlight, ProductSpecification,Wishlist,ProductReview,WishlistItem
)

# Improved CategorySerializer with proper image and product count handling
class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for product categories with improved image handling
    """
    parent_name = serializers.StringRelatedField(source='parent', read_only=True)
    image_url = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    primary_product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = (
            'id', 'name', 'slug', 'description', 'image', 'image_url', 
            'parent', 'parent_name', 'is_active', 'display_order', 
            'product_count', 'primary_product_image', 'created_at', 'updated_at'
        )
        read_only_fields = ('slug', 'created_at', 'updated_at')
    
    def get_image_url(self, obj):
        """
        Get the category image URL from the image field
        """
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_product_count(self, obj):
        """
        Get product count for this category, including subcategories
        """
        # Get direct products
        direct_count = obj.products.filter(is_active=True).count()
        
        # Get products from child categories
        subcategory_count = 0
        subcategories = Category.objects.filter(parent=obj.id)
        for subcategory in subcategories:
            subcategory_count += subcategory.products.filter(is_active=True).count()
        
        return direct_count + subcategory_count
    
    def get_primary_product_image(self, obj):
        """
        Get a product image to represent the category if category has no image
        This helps ensure we always have an image to display
        """
        if obj.image:
            # If category has its own image, no need for a product image
            return None
            
        # Try to get a product with a primary image
        request = self.context.get('request')
        
        # First try products directly in this category
        products = obj.products.filter(is_active=True)
        for product in products:
            primary_image = product.images.filter(is_primary=True).first()
            if primary_image and request:
                return request.build_absolute_uri(primary_image.image.url)
        
        # If no primary images found, try any product image
        for product in products:
            any_image = product.images.first()
            if any_image and request:
                return request.build_absolute_uri(any_image.image.url)
                
        # Try subcategories' products if needed
        subcategories = Category.objects.filter(parent=obj.id)
        for subcategory in subcategories:
            subcat_products = subcategory.products.filter(is_active=True)
            for product in subcat_products:
                primary_image = product.images.filter(is_primary=True).first()
                if primary_image and request:
                    return request.build_absolute_uri(primary_image.image.url)
                
                # Try any image
                any_image = product.images.first()
                if any_image and request:
                    return request.build_absolute_uri(any_image.image.url)
        
        return None


class CategoryListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for category lists
    """
    product_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    parent_name = serializers.StringRelatedField(source='parent', read_only=True)
    primary_product_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'product_count', 'image_url', 'parent', 'parent_name', 'primary_product_image')
    

    # def to_representation(self, instance):
    #     data = super().to_representation(instance)
        
    #     # Check if neither the category image nor any product image is available
    #     if data['primary_product_image'] is None:
    #         # Don't include this category in the response
    #         return None
        
    #     return data

    def get_product_count(self, obj):
        """
        Get product count for this category, including subcategories
        """
        # Get direct products
        direct_count = obj.products.filter(is_active=True).count()
        
        # Get products from child categories
        subcategory_count = 0
        subcategories = Category.objects.filter(parent=obj.id)
        for subcategory in subcategories:
            subcategory_count += subcategory.products.filter(is_active=True).count()
        
        return direct_count + subcategory_count
    
    def get_image_url(self, obj):
        """
        Get the category image URL
        """
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_primary_product_image(self, obj):
        """
        Get a product image to represent the category if category has no image
        """
        if obj.image:
            # If category has its own image, no need for a product image
            return None
            
        # Try to get a product with a primary image
        request = self.context.get('request')
        
        # First try products directly in this category
        products = obj.products.filter(is_active=True)
        for product in products:
            primary_image = product.images.filter(is_primary=True).first()
            if primary_image and request:
                return request.build_absolute_uri(primary_image.image.url)
        
        # If no primary images found, try any product image
        for product in products:
            any_image = product.images.first()
            if any_image and request:
                return request.build_absolute_uri(any_image.image.url)
                
        # Try subcategories' products if needed
        subcategories = Category.objects.filter(parent=obj.id)
        for subcategory in subcategories:
            subcat_products = subcategory.products.filter(is_active=True)
            for product in subcat_products:
                primary_image = product.images.filter(is_primary=True).first()
                if primary_image and request:
                    return request.build_absolute_uri(primary_image.image.url)
                
                # Try any image
                any_image = product.images.first()
                if any_image and request:
                    return request.build_absolute_uri(any_image.image.url)
        
        return None

class ColorSerializer(serializers.ModelSerializer):
    """
    Serializer for product colors
    """
    class Meta:
        model = Color
        fields = ('id', 'name', 'hex_value')


class SizeSerializer(serializers.ModelSerializer):
    """
    Serializer for product sizes
    """
    class Meta:
        model = Size
        fields = ('id', 'name', 'display_order', 'chest_measurement', 'length_measurement', 'sleeve_measurement')


class ProductSizeSerializer(serializers.ModelSerializer):
    """
    Serializer for product sizes with inventory info
    """
    size_name = serializers.StringRelatedField(source='size', read_only=True)
    size_details = SizeSerializer(source='size', read_only=True)
    
    class Meta:
        model = ProductSize
        fields = ('id', 'size', 'size_name', 'size_details', 'stock_quantity', 'is_available')


class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for product images
    """
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'image_url', 'alt_text', 'is_primary', 'display_order', 'color')
        read_only_fields = ('image_url',)
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None


class ProductHighlightSerializer(serializers.ModelSerializer):
    """
    Serializer for product highlights
    """
    class Meta:
        model = ProductHighlight
        fields = ('id', 'text', 'display_order')


class ProductSpecificationSerializer(serializers.ModelSerializer):
    """
    Serializer for product specifications
    """
    class Meta:
        model = ProductSpecification
        fields = ('id', 'title', 'value', 'display_order')


class ProductColorSerializer(serializers.ModelSerializer):
    """
    Serializer for product color variants
    """
    color_details = ColorSerializer(source='color', read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ProductColor
        fields = ('id', 'color', 'color_details', 'is_default', 'images')


class ProductListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for product listings
    """
    category_name = serializers.StringRelatedField(source='category', read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    price = serializers.FloatField()  # Ensure price is returned as a number
    original_price = serializers.FloatField(required=False, allow_null=True)  # Ensure original_price is a number
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'category', 'category_name', 
            'price', 'original_price', 'discount_percentage',
            'primary_image', 'is_new', 'is_bestseller',
            'in_stock', 'short_description', 'images'
        )
    
    def get_discount_percentage(self, obj):
        return obj.get_discount_percentage()
    
    def get_primary_image(self, obj):
        # Try to get the primary image
        primary_image = obj.images.filter(is_primary=True).first()
        if not primary_image:
            # Fallback to the first image
            primary_image = obj.images.first()
        
        if primary_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(primary_image.image.url)
        return None
    
    def get_images(self, obj):
        # Return a list of image URLs
        request = self.context.get('request')
        if request:
            return [
                request.build_absolute_uri(img.image.url) 
                for img in obj.images.all()
            ]
        return []


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for single product view
    """
    category = CategorySerializer(read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    highlights = ProductHighlightSerializer(many=True, read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    available_sizes = ProductSizeSerializer(source='productsize_set', many=True, read_only=True)
    colors = ProductColorSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    price = serializers.FloatField()  # Ensure price is returned as a number
    original_price = serializers.FloatField(required=False, allow_null=True)  # Ensure original_price is a number
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'category',
            'description', 'short_description',
            'price', 'original_price', 'discount_percentage',
            'fabric', 'fit', 'wash_care', 'model_size',
            'sku', 'in_stock', 'stock_quantity',
            'is_active', 'is_featured', 'is_new', 'is_bestseller',
            'highlights', 'specifications', 'available_sizes', 
            'colors', 'images', 'rating', 'reviews_count',
            'created_at', 'updated_at'
        )
        read_only_fields = ('slug', 'created_at', 'updated_at')
    
    def get_discount_percentage(self, obj):
        return obj.get_discount_percentage()
    
    def get_rating(self, obj):
        # Placeholder - you would implement this based on your review model
        # For now, returning a fixed rating of 4.5
        return 4.5
    
    def get_reviews_count(self, obj):
        # Placeholder - you would implement this based on your review model
        # For now, returning a fixed count of 12
        return 12


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating products (admin use)
    """
    highlights = ProductHighlightSerializer(many=True, required=False)
    specifications = ProductSpecificationSerializer(many=True, required=False)
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'category', 'description', 'short_description',
            'price', 'original_price', 'fabric', 'fit', 'wash_care', 
            'model_size', 'sku', 'in_stock', 'stock_quantity',
            'is_active', 'is_featured', 'is_new', 'is_bestseller',
            'highlights', 'specifications'
        )
    
    def create(self, validated_data):
        highlights_data = validated_data.pop('highlights', [])
        specifications_data = validated_data.pop('specifications', [])
        
        # Create the product
        product = Product.objects.create(**validated_data)
        
        # Create highlights
        for highlight_data in highlights_data:
            ProductHighlight.objects.create(product=product, **highlight_data)
        
        # Create specifications
        for spec_data in specifications_data:
            ProductSpecification.objects.create(product=product, **spec_data)
        
        return product
    
    def update(self, instance, validated_data):
        highlights_data = validated_data.pop('highlights', None)
        specifications_data = validated_data.pop('specifications', None)
        
        # Update the product fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update highlights if provided
        if highlights_data is not None:
            # Delete existing highlights
            instance.highlights.all().delete()
            # Create new highlights
            for highlight_data in highlights_data:
                ProductHighlight.objects.create(product=instance, **highlight_data)
        
        # Update specifications if provided
        if specifications_data is not None:
            # Delete existing specifications
            instance.specifications.all().delete()
            # Create new specifications
            for spec_data in specifications_data:
                ProductSpecification.objects.create(product=instance, **spec_data)
        
        return instance
    


# Wishlist Serializers
class WishlistItemSerializer(serializers.ModelSerializer):
    """
    Serializer for wishlist items
    """
    product_details = ProductListSerializer(source='product', read_only=True)
    
    class Meta:
        model = WishlistItem
        fields = ('id', 'product', 'product_details', 'selected_size', 'selected_color', 'notes', 'created_at')
        read_only_fields = ('id', 'created_at')


class WishlistSerializer(serializers.ModelSerializer):
    """
    Serializer for wishlists
    """
    items = WishlistItemSerializer(source='items.all', many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Wishlist
        fields = ('id', 'user', 'name', 'is_public', 'items', 'items_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def get_items_count(self, obj):
        return obj.items.count()


# Product Review Serializers
class ProductReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for product reviews
    """
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = (
            'id', 'product', 'user', 'user_name', 'rating', 'title', 
            'content', 'is_verified_purchase', 'is_approved', 
            'created_at'
        )
        read_only_fields = ('id', 'user', 'is_verified_purchase', 'is_approved', 'created_at')
    
    def get_user_name(self, obj):
        # Return first name or username
        return obj.user.get_full_name() or obj.user.username
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def create(self, validated_data):
        # Set user to current user
        validated_data['user'] = self.context['request'].user
        
        # Check if user has purchased this product
        # This would need to be implemented based on your order history
        # For now, we'll set it to False
        validated_data['is_verified_purchase'] = False
        
        return super().create(validated_data)