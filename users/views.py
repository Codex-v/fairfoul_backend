# users/views.py
from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.urls import reverse

from .models import Address
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer,
    UserPasswordChangeSerializer, AddressSerializer
)
from core.permissions import IsOwnerOrAdmin

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    Register a new user and send verification email
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer
    
    def perform_create(self, serializer):
        user = serializer.save()
        # Generate verification token
        token = default_token_generator.make_token(user)
        user.email_verification_token = token
        user.save()
        
        # Send verification email (in production, use a proper email service)
        if settings.EMAIL_HOST:  # Only send if email is configured
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            verification_link = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
            
            send_mail(
                'Verify your email address',
                f'Please click the link to verify your email: {verification_link}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_email(request, uidb64, token):
    """
    Verify user email with token
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_email_verified = True
        user.email_verification_token = None
        user.save()
        return Response({'detail': 'Email verified successfully.'}, status=status.HTTP_200_OK)
    else:
        return Response({'detail': 'Invalid verification link.'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update user profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """
    Change user password
    """
    serializer_class = UserPasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Check if current password is correct
        if not user.check_password(serializer.validated_data['current_password']):
            return Response({"current_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Generate new tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'detail': 'Password updated successfully.',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


class AddressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user addresses
    """
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        """
        Filter addresses to return only those belonging to the current user
        """
        return Address.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def default_shipping(self, request):
        """
        Get user's default shipping address
        """
        address = Address.objects.filter(
            user=request.user,
            is_default=True,
            address_type__in=['shipping', 'both']
        ).first()
        
        if address:
            serializer = self.get_serializer(address)
            return Response(serializer.data)
        return Response({'detail': 'No default shipping address found.'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def default_billing(self, request):
        """
        Get user's default billing address
        """
        address = Address.objects.filter(
            user=request.user,
            is_default=True,
            address_type__in=['billing', 'both']
        ).first()
        
        if address:
            serializer = self.get_serializer(address)
            return Response(serializer.data)
        return Response({'detail': 'No default billing address found.'}, status=status.HTTP_404_NOT_FOUND)