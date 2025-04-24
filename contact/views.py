from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.core.mail import send_mail
from django.conf import settings
from .models import ContactMessage
from .serializers import ContactMessageSerializer

class ContactMessageListCreateView(generics.ListCreateAPIView):
    """
    List all contact messages or create a new one
    """
    serializer_class = ContactMessageSerializer
    
    def get_permissions(self):
        """
        Admin users can view all messages
        Anonymous users can create messages
        """
        if self.request.method == 'POST':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        return ContactMessage.objects.all()
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        # Send notification email to admins
        if settings.EMAIL_HOST:  # Only send if email is configured
            subject = f"New Contact Message: {serializer.validated_data['subject']}"
            message = (
                f"Name: {serializer.validated_data['name']}\n"
                f"Email: {serializer.validated_data['email']}\n"
                f"Phone: {serializer.validated_data.get('phone', 'Not provided')}\n\n"
                f"Message:\n{serializer.validated_data['message']}"
            )
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],  # Send to admin email
                    fail_silently=True,
                )
            except Exception as e:
                # Log the error but don't fail the API call
                print(f"Error sending notification email: {e}")
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {"detail": "Your message has been sent successfully. We'll get back to you soon."},
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class ContactMessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a contact message
    """
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.IsAdminUser]