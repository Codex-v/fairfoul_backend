from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# API documentation setup
schema_view = get_schema_view(
    openapi.Info(
        title="FAIR FOUL API",
        default_version='v1',
        description="API documentation for FAIR FOUL e-commerce platform",
        terms_of_service="https://www.fairfoul.com/terms/",
        contact=openapi.Contact(email="contact@fairfoul.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin site
    path('admin/', admin.site.urls),
    
    # API v1 endpoints
    path('api/v1/', include([
        path('users/', include('users.urls')),
        path('products/', include('products.urls')),
        path('orders/', include('orders.urls')),
        path('contact/', include('contact.urls')),
        path('admin-console/', include('admin_console.urls')),  # Added admin console URLs
    ])),
    
    # API documentation
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]