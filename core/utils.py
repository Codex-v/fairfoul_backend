# core/utils.py
import uuid
import os
from django.utils.text import slugify

def get_unique_slug(model_instance, slug_field_name, sluggable_field_name):
    """
    Generate a unique slug for a model instance
    """
    slug = slugify(getattr(model_instance, sluggable_field_name))
    unique_slug = slug
    instance_class = model_instance.__class__
    
    # Check if the slug already exists
    counter = 1
    while instance_class._default_manager.filter(**{slug_field_name: unique_slug}).exists():
        unique_slug = f"{slug}-{counter}"
        counter += 1
        
    return unique_slug

def get_file_path(instance, filename):
    """
    Generate a unique filename for uploaded files
    """
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    model_name = instance.__class__.__name__.lower()
    
    return os.path.join(model_name, filename)