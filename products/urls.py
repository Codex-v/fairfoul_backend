# products/urls.py
from django.urls import path
from .views import (
    CategoryListView, CategoryDetailView, CategoryProductsView,
    ColorListCreateView, ColorDetailView,
    SizeListCreateView, SizeDetailView,
    ProductListCreateView, ProductDetailView, ProductRelatedView,
    FeaturedProductsView, BestsellerProductsView, NewArrivalsView,
    ProductImageListCreateView, ProductImageDetailView,
    ProductSizeListCreateView, ProductSizeDetailView,
    ProductColorListCreateView, ProductColorDetailView
)

urlpatterns = [
    # Category endpoints
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<slug:slug>/products/', CategoryProductsView.as_view(), name='category-products'),
    
    # Product endpoints
    path("product/",ProductListCreateView.as_view(),name="create-product"),
    path("product/<int:pk>/",ProductDetailView.as_view(),name="create-product"),


    # Color endpoints
    path('colors/', ColorListCreateView.as_view(), name='color-list'),
    path('colors/<int:pk>/', ColorDetailView.as_view(), name='color-detail'),
    
    # Size endpoints
    path('sizes/', SizeListCreateView.as_view(), name='size-list'),
    path('sizes/<int:pk>/', SizeDetailView.as_view(), name='size-detail'),
    
    # Product endpoints
    path('', ProductListCreateView.as_view(), name='product-list'),
    path('<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('<slug:slug>/related/', ProductRelatedView.as_view(), name='product-related'),
    path('featured/list/', FeaturedProductsView.as_view(), name='product-featured'),
    path('bestsellers/list/', BestsellerProductsView.as_view(), name='product-bestsellers'),
    path('new-arrivals/list/', NewArrivalsView.as_view(), name='product-new-arrivals'),
    
    # Admin-only endpoints
    path('admin/images/', ProductImageListCreateView.as_view(), name='product-image-list'),
    path('admin/images/<int:pk>/', ProductImageDetailView.as_view(), name='product-image-detail'),
    path('admin/product-sizes/', ProductSizeListCreateView.as_view(), name='product-size-list'),
    path('admin/product-sizes/<int:pk>/', ProductSizeDetailView.as_view(), name='product-size-detail'),
    path('admin/product-colors/', ProductColorListCreateView.as_view(), name='product-color-list'),
    path('admin/product-colors/<int:pk>/', ProductColorDetailView.as_view(), name='product-color-detail'),
]