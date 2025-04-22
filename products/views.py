# products/views.py
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Category, Color, Size, Product, ProductSize, 
    ProductColor, ProductImage, ProductHighlight, ProductSpecification
)
from .serializers import (
    CategorySerializer, CategoryListSerializer, ColorSerializer, SizeSerializer,
    ProductListSerializer, ProductDetailSerializer, ProductCreateUpdateSerializer,
    ProductImageSerializer, ProductSizeSerializer, ProductColorSerializer
)
from core.permissions import IsAdminUserOrReadOnly

class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for product categories
    """
    queryset = Category.objects.filter(is_active=True)
    permission_classes = [IsAdminUserOrReadOnly]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        return CategorySerializer
    
    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True)
        
        # Filter for top-level categories only (no parent)
        parent = self.request.query_params.get('parent')
        if parent == 'null':
            queryset = queryset.filter(parent__isnull=True)
        elif parent:
            queryset = queryset.filter(parent__slug=parent)
            
        return queryset.order_by('display_order', 'name')
    
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """
        Get products in this category
        """
        category = self.get_object()
        products = Product.objects.filter(category=category, is_active=True)
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
            
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)


class ColorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for colors
    """
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAdminUserOrReadOnly]


class SizeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for sizes
    """
    queryset = Size.objects.all().order_by('display_order')
    serializer_class = SizeSerializer
    permission_classes = [IsAdminUserOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for products
    """
    queryset = Product.objects.filter(is_active=True)
    permission_classes = [IsAdminUserOrReadOnly]
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_new', 'is_bestseller', 'in_stock']
    search_fields = ['name', 'description', 'short_description']
    ordering_fields = ['price', 'created_at', 'name']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        elif self.action == 'list':
            return ProductListSerializer
        return ProductDetailSerializer
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by size
        size = self.request.query_params.get('size')
        if size:
            queryset = queryset.filter(productsize__size__name=size, productsize__is_available=True)
        
        # Filter by color
        color = self.request.query_params.get('color')
        if color:
            queryset = queryset.filter(colors__color__name__iexact=color)
        
        # Default ordering
        ordering = self.request.query_params.get('ordering', '-created_at')
        if ordering == 'price_asc':
            queryset = queryset.order_by('price')
        elif ordering == 'price_desc':
            queryset = queryset.order_by('-price')
        elif ordering == 'newest':
            queryset = queryset.order_by('-created_at')
        elif ordering == 'bestseller':
            queryset = queryset.order_by('-is_bestseller', '-created_at')
        else:
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        """
        Get related products (same category)
        """
        product = self.get_object()
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        serializer = ProductListSerializer(
            related_products, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Get featured products
        """
        featured = Product.objects.filter(is_featured=True, is_active=True)[:8]
        serializer = ProductListSerializer(
            featured, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def bestsellers(self, request):
        """
        Get bestseller products
        """
        bestsellers = Product.objects.filter(is_bestseller=True, is_active=True)[:8]
        serializer = ProductListSerializer(
            bestsellers, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def new_arrivals(self, request):
        """
        Get new arrival products
        """
        new_arrivals = Product.objects.filter(is_new=True, is_active=True)[:8]
        serializer = ProductListSerializer(
            new_arrivals, many=True, context={'request': request}
        )
        return Response(serializer.data)


class ProductImageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for product images (admin only)
    """
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = ProductImage.objects.all()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        # Filter by color
        color_id = self.request.query_params.get('color')
        if color_id:
            queryset = queryset.filter(color_id=color_id)
        
        return queryset.order_by('display_order')


class ProductSizeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for product sizes (admin only)
    """
    queryset = ProductSize.objects.all()
    serializer_class = ProductSizeSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = ProductSize.objects.all()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset
    

class ProductColorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for product colors (admin only)
    """
    queryset = ProductColor.objects.all()
    serializer_class = ProductColorSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = ProductColor.objects.all()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset