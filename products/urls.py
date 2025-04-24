# products/urls.py - Updated with routes for wishlist and reviews
from django.urls import path
from .views import (
    CategoryListView, CategoryDetailView, CategoryProductsView,
    ColorListView, ColorDetailView,
    SizeListView, SizeDetailView,
    ProductListView, ProductDetailView, ProductRelatedView,
    FeaturedProductsView, BestsellerProductsView, NewArrivalsView
)
from .views_admin import (
    AdminProductListCreateView, AdminProductRetrieveUpdateDestroyView,
    AdminProductImageUploadView, AdminProductImageDeleteView, AdminProductImageSetPrimaryView,
    AdminProductImageBulkUploadView,
    AdminCategoryListCreateView, AdminCategoryRetrieveUpdateDestroyView,
    AdminColorListCreateView, AdminColorRetrieveUpdateDestroyView,
    AdminSizeListCreateView, AdminSizeRetrieveUpdateDestroyView,
    AdminProductSizeListCreateView, AdminProductSizeRetrieveUpdateDestroyView,
    AdminProductColorListCreateView, AdminProductColorRetrieveUpdateDestroyView
)
# Import the new views for wishlist and reviews
from .views import (
    WishlistListCreateView, WishlistDetailView, 
    WishlistItemCreateView, WishlistItemDetailView, AddToDefaultWishlistView,
    ProductReviewListCreateView, ProductReviewDetailView, UserReviewsListView
)

# User-facing URLs - Read-only operations
urlpatterns = [
    # Category endpoints
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<slug:slug>/products/', CategoryProductsView.as_view(), name='category-products'),
    
    # Color endpoints
    path('colors/', ColorListView.as_view(), name='color-list'),
    path('colors/<int:pk>/', ColorDetailView.as_view(), name='color-detail'),
    
    # Size endpoints
    path('sizes/', SizeListView.as_view(), name='size-list'),
    path('sizes/<int:pk>/', SizeDetailView.as_view(), name='size-detail'),
    
    # Product endpoints
    path('', ProductListView.as_view(), name='product-list'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('related/<slug:slug>/', ProductRelatedView.as_view(), name='product-related'),
    path('featured/', FeaturedProductsView.as_view(), name='product-featured'),
    path('bestsellers/', BestsellerProductsView.as_view(), name='product-bestsellers'),
    path('new-arrivals/', NewArrivalsView.as_view(), name='product-new-arrivals'),
    
    # NEW: Product Review endpoints (authenticated users only)
    path('product/<slug:slug>/reviews/', ProductReviewListCreateView.as_view(), name='product-reviews'),
    path('reviews/<int:pk>/', ProductReviewDetailView.as_view(), name='review-detail'),
    path('user/reviews/', UserReviewsListView.as_view(), name='user-reviews'),
    
    # NEW: Wishlist endpoints (authenticated users only)
    path('wishlists/', WishlistListCreateView.as_view(), name='wishlist-list'),
    path('wishlists/<int:pk>/', WishlistDetailView.as_view(), name='wishlist-detail'),
    path('wishlists/<int:wishlist_id>/items/', WishlistItemCreateView.as_view(), name='wishlist-add-item'),
    path('wishlists/<int:wishlist_id>/items/<int:pk>/', WishlistItemDetailView.as_view(), name='wishlist-item-detail'),
    path('add-to-wishlist/', AddToDefaultWishlistView.as_view(), name='add-to-default-wishlist'),
]

# Admin-only URLs - Create, Update, Delete operations
admin_urlpatterns = [
    # Admin Product endpoints
    path('admin/products/', AdminProductListCreateView.as_view(), name='admin-product-list'),
    path('admin/products/<slug:slug>/', AdminProductRetrieveUpdateDestroyView.as_view(), name='admin-product-detail'),
    
    # Admin Product Image endpoints
    path('admin/products/<slug:slug>/upload-image/', AdminProductImageUploadView.as_view(), name='admin-product-upload-image'),
    path('admin/products/<slug:slug>/delete-image/', AdminProductImageDeleteView.as_view(), name='admin-product-delete-image'),
    path('admin/products/<slug:slug>/set-primary-image/', AdminProductImageSetPrimaryView.as_view(), name='admin-product-set-primary-image'),
    path('admin/products/<slug:slug>/bulk-upload-images/', AdminProductImageBulkUploadView.as_view(), name='admin-product-bulk-upload-images'),
    
    # Admin Category endpoints
    path('admin/categories/', AdminCategoryListCreateView.as_view(), name='admin-category-list'),
    path('admin/categories/<slug:slug>/', AdminCategoryRetrieveUpdateDestroyView.as_view(), name='admin-category-detail'),
    
    # Admin Color endpoints
    path('admin/colors/', AdminColorListCreateView.as_view(), name='admin-color-list'),
    path('admin/colors/<int:pk>/', AdminColorRetrieveUpdateDestroyView.as_view(), name='admin-color-detail'),
    
    # Admin Size endpoints
    path('admin/sizes/', AdminSizeListCreateView.as_view(), name='admin-size-list'),
    path('admin/sizes/<int:pk>/', AdminSizeRetrieveUpdateDestroyView.as_view(), name='admin-size-detail'),
    
    # Admin Product Size endpoints
    path('admin/product-sizes/', AdminProductSizeListCreateView.as_view(), name='admin-product-size-list'),
    path('admin/product-sizes/<int:pk>/', AdminProductSizeRetrieveUpdateDestroyView.as_view(), name='admin-product-size-detail'),
    
    # Admin Product Color endpoints
    path('admin/product-colors/', AdminProductColorListCreateView.as_view(), name='admin-product-color-list'),
    path('admin/product-colors/<int:pk>/', AdminProductColorRetrieveUpdateDestroyView.as_view(), name='admin-product-color-detail'),
]

# Combine user and admin URLs
urlpatterns += admin_urlpatterns