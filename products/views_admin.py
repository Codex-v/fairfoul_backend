# products/views_admin.py
from rest_framework import generics, status, parsers
from rest_framework.views import APIView
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
    ProductColorSerializer, ColorSerializer, SizeSerializer, CategorySerializer,
    ProductCreateUpdateSerializer
)

class AdminProductListCreateView(generics.ListCreateAPIView):
    """
    Admin-only view for listing and creating products
    """
    permission_classes = [IsAdminUser]
    queryset = Product.objects.all().order_by('-created_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
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


class AdminProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin-only view for retrieving, updating and deleting products
    """
    permission_classes = [IsAdminUser]
    lookup_field = 'slug'
    queryset = Product.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
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


class AdminProductImageUploadView(APIView):
    """
    Admin-only view for uploading product images
    """
    permission_classes = [IsAdminUser]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def post(self, request, slug=None):
        """
        Upload an image for a product
        """
        product = get_object_or_404(Product, slug=slug)
        
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


class AdminProductImageDeleteView(APIView):
    """
    Admin-only view for deleting product images
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, slug=None):
        """
        Delete a product image
        """
        product = get_object_or_404(Product, slug=slug)
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


class AdminProductImageSetPrimaryView(APIView):
    """
    Admin-only view for setting a product image as primary
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, slug=None):
        """
        Set an image as the primary image for a product or color
        """
        product = get_object_or_404(Product, slug=slug)
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


class AdminProductImageBulkUploadView(APIView):
    """
    Admin-only view for bulk uploading product images
    """
    permission_classes = [IsAdminUser]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def post(self, request, slug=None):
        """
        Upload multiple images at once for a product
        """
        product = get_object_or_404(Product, slug=slug)
        
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
            serializer = ProductImageSerializer(product_image, context={'request': request})
            created_images.append(serializer.data)
        
        return Response(created_images, status=status.HTTP_201_CREATED)


# Admin-only views for categories
class AdminCategoryListCreateView(generics.ListCreateAPIView):
    """
    Admin-only view for listing and creating categories
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]



class AdminCategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin-only view for retrieving, updating and deleting categories
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]
    lookup_field = 'slug'


# Admin-only views for colors
class AdminColorListCreateView(generics.ListCreateAPIView):
    """
    Admin-only view for listing and creating colors
    """
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAdminUser]


class AdminColorRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin-only view for retrieving, updating and deleting colors
    """
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAdminUser]


# Admin-only views for sizes
class AdminSizeListCreateView(generics.ListCreateAPIView):
    """
    Admin-only view for listing and creating sizes
    """
    queryset = Size.objects.all().order_by('display_order')
    serializer_class = SizeSerializer
    permission_classes = [IsAdminUser]


class AdminSizeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin-only view for retrieving, updating and deleting sizes
    """
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    permission_classes = [IsAdminUser]


# Admin-only views for product sizes
class AdminProductSizeListCreateView(generics.ListCreateAPIView):
    """
    Admin-only view for listing and creating product sizes
    """
    serializer_class = ProductSizeSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = ProductSize.objects.all()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset


class AdminProductSizeRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin-only view for retrieving, updating and deleting product sizes
    """
    queryset = ProductSize.objects.all()
    serializer_class = ProductSizeSerializer
    permission_classes = [IsAdminUser]


# Admin-only views for product colors
class AdminProductColorListCreateView(generics.ListCreateAPIView):
    """
    Admin-only view for listing and creating product colors
    """
    serializer_class = ProductColorSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = ProductColor.objects.all()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset


class AdminProductColorRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Admin-only view for retrieving, updating and deleting product colors
    """
    queryset = ProductColor.objects.all()
    serializer_class = ProductColorSerializer
    permission_classes = [IsAdminUser]