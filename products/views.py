# products/views.py
from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.shortcuts import get_object_or_404
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

# Category Views
class CategoryListView(generics.ListCreateAPIView):
    """
    List all categories or create a new one
    """
    permission_classes = [IsAdminUserOrReadOnly]
    serializer_class = CategoryListSerializer
    
    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True)
        
        # Filter for top-level categories only (no parent)
        parent = self.request.query_params.get('parent')
        if parent == 'null':
            queryset = queryset.filter(parent__isnull=True)
        elif parent:
            queryset = queryset.filter(parent__slug=parent)
            
        return queryset.order_by('display_order', 'name')


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a category
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUserOrReadOnly]
    lookup_field = 'slug'


class CategoryProductsView(generics.ListAPIView):
    """
    List products in a specific category
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        category_slug = self.kwargs.get('slug')
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        return Product.objects.filter(category=category, is_active=True)


# Color Views
class ColorListCreateView(generics.ListCreateAPIView):
    """
    List all colors or create a new one
    """
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAdminUserOrReadOnly]


class ColorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a color
    """
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [IsAdminUserOrReadOnly]


# Size Views
class SizeListCreateView(generics.ListCreateAPIView):
    """
    List all sizes or create a new one
    """
    queryset = Size.objects.all().order_by('display_order')
    serializer_class = SizeSerializer
    permission_classes = [IsAdminUserOrReadOnly]


class SizeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a size
    """
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    permission_classes = [IsAdminUserOrReadOnly]


# Product Views
class ProductListCreateView(generics.ListCreateAPIView):
    """
    List all products or create a new one
    """
    permission_classes = [IsAdminUserOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_new', 'is_bestseller', 'in_stock']
    search_fields = ['name', 'description', 'short_description']
    ordering_fields = ['price', 'created_at', 'name']
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ProductCreateUpdateSerializer
        return ProductListSerializer
    
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


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product
    """
    permission_classes = [IsAdminUserOrReadOnly]
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True)


class ProductRelatedView(generics.ListAPIView):
    """
    List related products for a specific product
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        product = get_object_or_404(Product, slug=slug, is_active=True)
        return Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]


class FeaturedProductsView(generics.ListAPIView):
    """
    List featured products
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return Product.objects.filter(is_featured=True, is_active=True)[:8]


class BestsellerProductsView(generics.ListAPIView):
    """
    List bestseller products
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return Product.objects.filter(is_bestseller=True, is_active=True)[:8]


class NewArrivalsView(generics.ListAPIView):
    """
    List new arrival products
    """
    serializer_class = ProductListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return Product.objects.filter(is_new=True, is_active=True)[:8]


# Admin-only views for product management
class ProductImageListCreateView(generics.ListCreateAPIView):
    """
    List all product images or create a new one (admin only)
    """
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


class ProductImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product image (admin only)
    """
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [permissions.IsAdminUser]


class ProductSizeListCreateView(generics.ListCreateAPIView):
    """
    List all product sizes or create a new one (admin only)
    """
    serializer_class = ProductSizeSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = ProductSize.objects.all()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset


class ProductSizeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product size (admin only)
    """
    queryset = ProductSize.objects.all()
    serializer_class = ProductSizeSerializer
    permission_classes = [permissions.IsAdminUser]


class ProductColorListCreateView(generics.ListCreateAPIView):
    """
    List all product colors or create a new one (admin only)
    """
    serializer_class = ProductColorSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = ProductColor.objects.all()
        
        # Filter by product
        product_id = self.request.query_params.get('product')
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset


class ProductColorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a product color (admin only)
    """
    queryset = ProductColor.objects.all()
    serializer_class = ProductColorSerializer
    permission_classes = [permissions.IsAdminUser]