# users/urls.py
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from .views import (
    RegisterView, UserProfileView, ChangePasswordView,
    verify_email, AddressListCreateView, AddressDetailView,
    DefaultShippingAddressView, DefaultBillingAddressView
)

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('auth/verify-email/<str:uidb64>/<str:token>/', verify_email, name='verify_email'),
    
    # User profile endpoints
    path('profile/', UserProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Address endpoints
    path('addresses/', AddressListCreateView.as_view(), name='address-list'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),
    path('addresses/default-shipping/', DefaultShippingAddressView.as_view(), name='default-shipping-address'),
    path('addresses/default-billing/', DefaultBillingAddressView.as_view(), name='default-billing-address'),
]