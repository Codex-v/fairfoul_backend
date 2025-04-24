# products/views.py - Updated to contain only read-only views for regular users
from rest_framework import generics, permissions, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Category, Color, Size, Product, ProductSize, 
    ProductColor, ProductImage, ProductHighlight, ProductSpecification
)
from .serializers import (
    CategorySerializer, CategoryListSerializer, ColorSerializer, SizeSerializer,
    ProductListSerializer, ProductDetailSerializer,
    ProductImageSerializer, ProductSizeSerializer, ProductColorSerializer
)

# Category Views
class CategoryListView(generics.ListAPIView):
    """
    List all categories with images (either their own or from products)
    """
    serializer_class = CategoryListSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True)
        
        # Filter for top-level categories only (no parent)
        parent = self.request.query_params.get('parent')
        if parent == 'null':
            queryset = queryset.filter(parent__isnull=True)
        elif parent:
            queryset = queryset.filter(parent__slug=parent)
        
        # Filter to include only categories with images or with products that have images
        queryset = queryset.filter(
            # Categories with their own image
            Q(image__isnull=False) & ~Q(image='') |
            # Categories with products that have images
            Q(products__images__isnull=False)
        ).distinct()
        
        return queryset.order_by('display_order', 'name')


class CategoryDetailView(generics.RetrieveAPIView):
    """
    Retrieve a category
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
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
class ColorListView(generics.ListAPIView):
    """
    List all colors
    """
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [permissions.AllowAny]


class ColorDetailView(generics.RetrieveAPIView):
    """
    Retrieve a color
    """
    queryset = Color.objects.all()
    serializer_class = ColorSerializer
    permission_classes = [permissions.AllowAny]


# Size Views
class SizeListView(generics.ListAPIView):
    """
    List all sizes
    """
    queryset = Size.objects.all().order_by('display_order')
    serializer_class = SizeSerializer
    permission_classes = [permissions.AllowAny]


class SizeDetailView(generics.RetrieveAPIView):
    """
    Retrieve a size
    """
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    permission_classes = [permissions.AllowAny]


# Product Views
class ProductListView(generics.ListAPIView):
    """
    List all products
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_new', 'is_bestseller', 'in_stock']
    search_fields = ['name', 'description', 'short_description']
    ordering_fields = ['price', 'created_at', 'name']
    
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


class ProductDetailView(generics.RetrieveAPIView):
    """
    Retrieve a product
    """
    permission_classes = [permissions.AllowAny]
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    
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


# products/views_user.py - Add views for authenticated users to manage wishlist and reviews
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import (
    Product, Wishlist, WishlistItem, ProductReview
)
from .serializers import (
    WishlistSerializer, WishlistItemSerializer, ProductReviewSerializer
)

# Custom permission class for wishlist operations
class IsWishlistOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of a wishlist to view or edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the wishlist
        return obj.user == request.user

# Wishlist Views
class WishlistListCreateView(generics.ListCreateAPIView):
    """
    List all wishlists for the current user or create a new wishlist
    """
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WishlistDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a wishlist
    """
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated, IsWishlistOwner]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)


class WishlistItemCreateView(generics.CreateAPIView):
    """
    Add a product to a wishlist
    """
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # Get the wishlist
        wishlist_id = self.kwargs.get('wishlist_id')
        wishlist = get_object_or_404(Wishlist, id=wishlist_id, user=self.request.user)
        
        # Save the wishlist item
        serializer.save(wishlist=wishlist)


class WishlistItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a wishlist item
    """
    serializer_class = WishlistItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        wishlist_id = self.kwargs.get('wishlist_id')
        return WishlistItem.objects.filter(wishlist__id=wishlist_id, wishlist__user=self.request.user)


class AddToDefaultWishlistView(APIView):
    """
    Add a product to the user's default wishlist (creates a default wishlist if none exists)
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        # Get product ID from request data
        product_id = request.data.get('product_id')
        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create default wishlist
        default_wishlist, created = Wishlist.objects.get_or_create(
            user=request.user,
            name="Default",
            defaults={'is_public': False}
        )
        
        # Get other optional parameters
        selected_size = request.data.get('selected_size')
        selected_color = request.data.get('selected_color')
        notes = request.data.get('notes', '')
        
        # Check if product exists
        product = get_object_or_404(Product, id=product_id)
        
        # Check if item already exists in wishlist
        existing_item = WishlistItem.objects.filter(
            wishlist=default_wishlist,
            product=product
        ).first()
        
        if existing_item:
            # Update existing item
            existing_item.selected_size = selected_size
            existing_item.selected_color = selected_color
            existing_item.notes = notes
            existing_item.save()
            serializer = WishlistItemSerializer(existing_item)
            return Response(serializer.data)
        else:
            # Create new item
            wishlist_item = WishlistItem.objects.create(
                wishlist=default_wishlist,
                product=product,
                selected_size=selected_size,
                selected_color=selected_color,
                notes=notes
            )
            serializer = WishlistItemSerializer(wishlist_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)


# Product Review Views
class ProductReviewListCreateView(generics.ListCreateAPIView):
    """
    List all reviews for a product or create a new review
    """
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        product_slug = self.kwargs.get('slug')
        return ProductReview.objects.filter(
            product__slug=product_slug,
            is_approved=True
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        # Get the product
        product_slug = self.kwargs.get('slug')
        product = get_object_or_404(Product, slug=product_slug)
        
        # Check if user has already reviewed this product
        existing_review = ProductReview.objects.filter(
            product=product,
            user=self.request.user
        ).exists()
        
        if existing_review:
            from rest_framework.exceptions import ValidationError
            raise ValidationError("You have already reviewed this product")
        
        # Save the review
        serializer.save(
            product=product, 
            user=self.request.user,
            # You could implement logic here to check if user has purchased the product
            is_verified_purchase=False
        )


class ProductReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a review
    """
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # User can only access their own reviews
        return ProductReview.objects.filter(user=self.request.user)


class UserReviewsListView(generics.ListAPIView):
    """
    List all reviews by the current user
    """
    serializer_class = ProductReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ProductReview.objects.filter(
            user=self.request.user
        ).order_by('-created_at')