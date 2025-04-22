# contact/models.py
from django.db import models
from core.models import TimestampedModel

class ContactMessage(TimestampedModel):
    """
    Model for storing contact form messages
    """
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.subject} - {self.name}"
    
    class Meta:
        ordering = ['-created_at']


# contact/serializers.py
from rest_framework import serializers
from .models import ContactMessage

class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for contact messages
    """
    class Meta:
        model = ContactMessage
        fields = ('id', 'name', 'email', 'phone', 'subject', 'message', 'created_at')
        read_only_fields = ('created_at',)