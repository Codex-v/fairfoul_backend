# products/views_admin.py
from rest_framework import viewsets, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import (
    Product, ProductImage, ProductSize, ProductColor,
    ProductHighlight, ProductSpecification, Color, Size, Category
)
from .serializers import (
    ProductDetailSerializer, ProductImageSerializer, ProductSizeSerializer, 
    ProductColorSerializer, ColorSerializer, SizeSerializer, CategorySerializer
)
from .serializers_admin import (
    ProductCreateUpdateSerializer, AdminProductSizeSerializer, AdminProductColorSerializer
)

class AdminProductViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for product management
    """
    permission_classes = [IsAdminUser]
    lookup_field = 'slug'
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def get_queryset(self):
        return Product.objects.all().order_by('-created_at')
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Create a new product with associated data (sizes, colors, specs, highlights)
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save the product
        product = serializer.save()
        
        # Process sizes
        sizes = request.data.get('sizes', [])
        if isinstance(sizes, list):
            for size_id in sizes:
                size = get_object_or_404(Size, id=size_id)
                ProductSize.objects.create(
                    product=product,
                    size=size,
                    is_available=True,
                    stock_quantity=product.stock_quantity  # Default to product stock
                )
        
        # Process colors
        colors = request.data.get('colors', [])
        if isinstance(colors, list):
            for i, color_id in enumerate(colors):
                color = get_object_or_404(Color, id=color_id)
                is_default = i == 0  # Make first color the default
                ProductColor.objects.create(
                    product=product,
                    color=color,
                    is_default=is_default
                )
        
        # Return the product data
        output_serializer = ProductDetailSerializer(
            product, context={'request': request}
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        Update a product with associated data
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Save the product
        product = serializer.save()
        
        # Update sizes if provided
        sizes = request.data.get('sizes')
        if sizes is not None:
            # Clear existing sizes
            ProductSize.objects.filter(product=product).delete()
            
            # Add new sizes
            if isinstance(sizes, list):
                for size_id in sizes:
                    size = get_object_or_404(Size, id=size_id)
                    ProductSize.objects.create(
                        product=product,
                        size=size,
                        is_available=True,
                        stock_quantity=product.stock_quantity  # Default to product stock
                    )
        
        # Update colors if provided
        colors = request.data.get('colors')
        if colors is not None:
            # Clear existing colors (but keep the images linked to colors)
            ProductColor.objects.filter(product=product).delete()
            
            # Add new colors
            if isinstance(colors, list):
                for i, color_id in enumerate(colors):
                    color = get_object_or_404(Color, id=color_id)
                    is_default = i == 0  # Make first color the default
                    ProductColor.objects.create(
                        product=product,
                        color=color,
                        is_default=is_default
                    )
        
        # Return the updated product data
        output_serializer = ProductDetailSerializer(
            product, context={'request': request}
        )
        return Response(output_serializer.data)
    
    @action(detail=True, methods=['post'])
    def upload_image(self, request, slug=None):
        """
        Upload an image for a product
        """
        product = self.get_object()
        
        # Get image parameters
        image = request.FILES.get('image')
        alt_text = request.data.get('alt_text', '')
        is_primary = request.data.get('is_primary') in ['true', 'True', True]
        display_order = request.data.get('display_order', 0)
        color_id = request.data.get('color')
        
        if not image:
            return Response(
                {'error': 'No image provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the color if provided
        color = None
        if color_id:
            try:
                color = ProductColor.objects.get(product=product, color_id=color_id)
            except ProductColor.DoesNotExist:
                return Response(
                    {'error': 'Invalid color ID for this product'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # If this image is set as primary, unset other primary images
        if is_primary:
            if color:
                # If color-specific, only unset primary for this color
                ProductImage.objects.filter(
                    product=product,
                    color=color,
                    is_primary=True
                ).update(is_primary=False)
            else:
                # If not color-specific, unset primary for all non-color images
                ProductImage.objects.filter(
                    product=product,
                    color__isnull=True,
                    is_primary=True
                ).update(is_primary=False)
        
        # Create new image
        product_image = ProductImage.objects.create(
            product=product,
            color=color,
            image=image,
            alt_text=alt_text,
            is_primary=is_primary,
            display_order=display_order
        )
        
        serializer = ProductImageSerializer(
            product_image, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['delete', 'post'])
    def delete_image(self, request, slug=None):
        """
        Delete a product image
        """
        product = self.get_object()
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response(
                {'error': 'No image ID provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            image = ProductImage.objects.get(id=image_id, product=product)
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProductImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def set_primary_image(self, request, slug=None):
        """
        Set an image as the primary image for a product or color
        """
        product = self.get_object()
        image_id = request.data.get('image_id')
        
        if not image_id:
            return Response(
                {'error': 'No image ID provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            image = ProductImage.objects.get(id=image_id, product=product)
            
            # Unset other primary images
            if image.color:
                # If color-specific, only unset primary for this color
                ProductImage.objects.filter(
                    product=product,
                    color=image.color,
                    is_primary=True
                ).exclude(id=image.id).update(is_primary=False)
            else:
                # If not color-specific, unset primary for all non-color images
                ProductImage.objects.filter(
                    product=product,
                    color__isnull=True,
                    is_primary=True
                ).exclude(id=image.id).update(is_primary=False)
            
            # Set this image as primary
            image.is_primary = True
            image.save()
            
            return Response(
                ProductImageSerializer(image, context={'request': request}).data
            )
        except ProductImage.DoesNotExist:
            return Response(
                {'error': 'Image not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class AdminCategoryViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for category management
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'slug'


class AdminColorViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for color management
    """
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAdminUser]


class AdminSizeViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for size management
    """
    queryset = Size.objects.all().order_by('display_order')
    serializer_class = SizeSerializer
    permission_classes = [IsAdminUser]


class AdminProductSizeViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for product size management
    """
    queryset = ProductSize.objects.all()
    serializer_class = AdminProductSizeSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset


class AdminProductColorViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for product color management
    """
    queryset = ProductColor.objects.all()
    serializer_class = AdminProductColorSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset


class AdminProductImageViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for product image management
    """
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by color
        color_id = self.request.query_params.get('color')
        if color_id:
            queryset = queryset.filter(color_id=color_id)
        
        return queryset.order_by('display_order')
    

    # Continue AdminProductImageViewSet class

    def create(self, request, *args, **kwargs):
        """
        Create a new product image with proper association to product and optional color
        """
        # Validate required fields
        product_id = request.data.get('product')
        if not product_id:
            return Response(
                {'error': 'Product ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get product
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Handle optional color association
        color = None
        color_id = request.data.get('color')
        if color_id:
            try:
                color = ProductColor.objects.get(product=product, color_id=color_id)
            except ProductColor.DoesNotExist:
                return Response(
                    {'error': 'Invalid color for this product'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if this image should be primary
        is_primary = request.data.get('is_primary') == 'true'
        if is_primary:
            # If setting as primary, reset other primary images
            if color:
                # For color-specific images
                ProductImage.objects.filter(
                    product=product, 
                    color=color, 
                    is_primary=True
                ).update(is_primary=False)
            else:
                # For non-color-specific images
                ProductImage.objects.filter(
                    product=product, 
                    color__isnull=True, 
                    is_primary=False
                ).update(is_primary=False)
        
        # Continue with standard creation
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """
        Update a product image
        """
        # Check if updating primary status
        is_primary = request.data.get('is_primary')
        if is_primary == 'true':
            instance = self.get_object()
            
            # Handle primary status for the relevant image group
            if instance.color:
                # Color-specific image
                ProductImage.objects.filter(
                    product=instance.product, 
                    color=instance.color, 
                    is_primary=True
                ).exclude(pk=instance.pk).update(is_primary=False)
            else:
                # Non-color-specific image
                ProductImage.objects.filter(
                    product=instance.product, 
                    color__isnull=True, 
                    is_primary=True
                ).exclude(pk=instance.pk).update(is_primary=False)
        
        return super().update(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """
        Upload multiple images at once for a product
        """
        # Validate product
        product_id = request.data.get('product')
        if not product_id:
            return Response(
                {'error': 'Product ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get color if provided
        color = None
        color_id = request.data.get('color')
        if color_id:
            try:
                color = ProductColor.objects.get(product=product, color_id=color_id)
            except ProductColor.DoesNotExist:
                return Response(
                    {'error': 'Invalid color for this product'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get files from request
        images = request.FILES.getlist('images')
        if not images:
            return Response(
                {'error': 'No images provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if we have existing images
        has_existing_images = ProductImage.objects.filter(
            product=product,
            color=color
        ).exists()
        
        # Process and save each image
        created_images = []
        for i, image_file in enumerate(images):
            # Set first image as primary if no existing images
            is_primary = not has_existing_images and i == 0
            
            # Create image
            product_image = ProductImage.objects.create(
                product=product,
                color=color,
                image=image_file,
                alt_text=request.data.get('alt_text', '') or f"{product.name} image {i+1}",
                is_primary=is_primary,
                display_order=request.data.get('display_order', 0) or i
            )
            
            # Serialize and add to result list
            serializer = self.get_serializer(product_image)
            created_images.append(serializer.data)
        
        return Response(created_images, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """
        Set an image as the primary image for a product or color
        """
        # Get the image
        image = self.get_object()
        
        # Reset primary status on other images in the same group
        if image.color:
            # Color-specific image
            ProductImage.objects.filter(
                product=image.product,
                color=image.color,
                is_primary=True
            ).exclude(pk=image.pk).update(is_primary=False)
        else:
            # Non-color-specific image
            ProductImage.objects.filter(
                product=image.product,
                color__isnull=True,
                is_primary=True
            ).exclude(pk=image.pk).update(is_primary=False)
        
        # Set this image as primary
        image.is_primary = True
        image.save()
        
        serializer = self.get_serializer(image)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_display_order(self, request, pk=None):
        """
        Update the display order of an image
        """
        # Get the image
        image = self.get_object()
        
        # Get new display order
        display_order = request.data.get('display_order')
        if display_order is None:
            return Response(
                {'error': 'Display order is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            display_order = int(display_order)
        except ValueError:
            return Response(
                {'error': 'Display order must be a number'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update display order
        image.display_order = display_order
        image.save()
        
        serializer = self.get_serializer(image)
        return Response(serializer.data)