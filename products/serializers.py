# products/serializers.py
from rest_framework import serializers
from .models import (
    Category, Color, Size, Product, ProductSize, 
    ProductColor, ProductImage, ProductHighlight, ProductSpecification
)

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for product categories
    """
    parent_name = serializers.StringRelatedField(source='parent', read_only=True)
    image_url = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = (
            'id', 'name', 'slug', 'description', 'image', 'image_url', 
            'parent', 'parent_name', 'is_active', 'display_order', 
            'product_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('slug', 'created_at', 'updated_at')
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class CategoryListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for category lists
    """
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'product_count')
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


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
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'category', 'category_name', 
            'price', 'original_price', 'discount_percentage',
            'primary_image', 'is_new', 'is_bestseller',
            'in_stock', 'short_description'
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


class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for single product view
    """
    category_name = serializers.StringRelatedField(source='category', read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    highlights = ProductHighlightSerializer(many=True, read_only=True)
    specifications = ProductSpecificationSerializer(many=True, read_only=True)
    available_sizes = ProductSizeSerializer(source='productsize_set', many=True, read_only=True)
    colors = ProductColorSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'category', 'category_name', 
            'description', 'short_description',
            'price', 'original_price', 'discount_percentage',
            'fabric', 'fit', 'wash_care', 'model_size',
            'sku', 'in_stock', 'stock_quantity',
            'is_active', 'is_featured', 'is_new', 'is_bestseller',
            'highlights', 'specifications', 'available_sizes', 
            'colors', 'images', 'created_at', 'updated_at'
        )
        read_only_fields = ('slug', 'created_at', 'updated_at')
    
    def get_discount_percentage(self, obj):
        return obj.get_discount_percentage()


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