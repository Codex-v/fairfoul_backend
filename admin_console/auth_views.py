# admin_console/auth_views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from .models import AdminActivity

User = get_user_model()

class AdminLoginView(APIView):
    """
    Admin-specific login view that checks for staff privileges
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'detail': 'Email and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Authenticate user
        user = authenticate(request, username=email, password=password)
        
        if user is None:
            return Response(
                {'detail': 'Invalid credentials.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user is staff
        if not user.is_staff:
            return Response(
                {'detail': 'You do not have admin privileges.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Prepare user data
        user_data = {
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        
        # Log admin login activity
        client_ip = request.META.get('REMOTE_ADDR', '')
        AdminActivity.objects.create(
            user=user,
            activity_type='login',
            description=f'Admin login from {client_ip}',
            ip_address=client_ip
        )
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': user_data
        })


class AdminLogoutView(APIView):
    """
    Admin logout view that logs the activity
    """
    
    def post(self, request):
        # Log admin logout activity
        client_ip = request.META.get('REMOTE_ADDR', '')
        AdminActivity.objects.create(
            user=request.user,
            activity_type='logout',
            description=f'Admin logout from {client_ip}',
            ip_address=client_ip
        )
        
        return Response({'detail': 'Logout successful.'})


class AdminVerifyTokenView(APIView):
    """
    Verify that a token belongs to a staff user
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'detail': 'No token provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from rest_framework_simplejwt.tokens import AccessToken
            from rest_framework_simplejwt.exceptions import TokenError
            
            # Decode token
            decoded_token = AccessToken(token)
            user_id = decoded_token['user_id']
            
            # Get user from database
            user = User.objects.get(id=user_id)
            
            # Check if user is staff
            if not user.is_staff:
                return Response(
                    {'detail': 'You do not have admin privileges.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return Response({'is_valid': True, 'is_staff': True})
            
        except (TokenError, User.DoesNotExist):
            return Response(
                {'detail': 'Invalid token.'},
                status=status.HTTP_401_UNAUTHORIZED
            )