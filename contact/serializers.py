from rest_framework import serializers
from .models import ContactMessage
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class ContactMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for contact messages
    """
    class Meta:
        model = ContactMessage
        fields = ('id', 'name', 'email', 'phone', 'subject', 'message', 'created_at')
        read_only_fields = ('created_at',)

    def validate_email(self, value):
        """
        Validate the email field
        """
        if not value:
            raise ValidationError(_("Email is required."))
        return value

    def validate_phone(self, value):
        """
        Validate the phone field
        """
        if not value:
            raise ValidationError(_("Phone number is required."))
        return value
    def validate(self, data):
        """
        Validate the entire data
        """
        if not data.get('name'):
            raise ValidationError(_("Name is required."))
        if not data.get('subject'):
            raise ValidationError(_("Subject is required."))
        if not data.get('message'):
            raise ValidationError(_("Message is required."))
        return data
    def create(self, validated_data):
        """
        Create a new contact message
        """
        contact_message = ContactMessage.objects.create(**validated_data)
        return contact_message
    def update(self, instance, validated_data):
        """
        Update an existing contact message
        """
        instance.name = validated_data.get('name', instance.name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.subject = validated_data.get('subject', instance.subject)
        instance.message = validated_data.get('message', instance.message)
        instance.save()
        return instance
    def delete(self, instance):
        """
        Delete a contact message
        """
        instance.delete()
        return instance
