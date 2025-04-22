# products/models.py
from django.db import models
from django.core.validators import MinValueValidator
from django.utils.text import slugify
from core.models import TimestampedModel
from core.utils import get_file_path

class Category(TimestampedModel):
    """
    Product category model
    """
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Color(models.Model):
    """
    Product color model
    """
    name = models.CharField(max_length=50)
    hex_value = models.CharField(max_length=7)  # Format: #RRGGBB
    
    def __str__(self):
        return self.name


class Size(models.Model):
    """
    Product size model
    """
    name = models.CharField(max_length=10)  # S, M, L, XL, etc.
    display_order = models.PositiveSmallIntegerField(default=0)
    
    # Size measurements
    chest_measurement = models.CharField(max_length=20, blank=True, null=True)
    length_measurement = models.CharField(max_length=20, blank=True, null=True)
    sleeve_measurement = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        ordering = ['display_order']
    
    def __str__(self):
        return self.name


class Product(TimestampedModel):
    """
    Product model
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    description = models.TextField()
    short_description = models.CharField(max_length=255, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Product specs
    fabric = models.CharField(max_length=100, blank=True)
    fit = models.CharField(max_length=100, blank=True)
    wash_care = models.CharField(max_length=255, blank=True)
    model_size = models.CharField(max_length=100, blank=True)
    
    # Inventory
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    in_stock = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    
    # Visibility flags
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    
    # Available sizes
    sizes = models.ManyToManyField(Size, through='ProductSize')
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_discount_percentage(self):
        """Calculate discount percentage if original price exists"""
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0


class ProductSize(models.Model):
    """
    Many-to-many relationship between Product and Size with inventory tracking
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('product', 'size')
    
    def __str__(self):
        return f"{self.product.name} - {self.size.name}"


class ProductColor(models.Model):
    """
    Product color variant with associated images
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='colors')
    color = models.ForeignKey(Color, on_delete=models.CASCADE)
    is_default = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('product', 'color')
    
    def __str__(self):
        return f"{self.product.name} - {self.color.name}"
    
    def save(self, *args, **kwargs):
        # If this color is being set as default, unset any existing defaults for this product
        if self.is_default:
            ProductColor.objects.filter(
                product=self.product,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """
    Product image model
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    color = models.ForeignKey(ProductColor, on_delete=models.SET_NULL, null=True, blank=True, related_name='images')
    image = models.ImageField(upload_to=get_file_path)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order']
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def save(self, *args, **kwargs):
        # If this image is being set as primary, unset any existing primary images for this product/color
        if self.is_primary:
            if self.color:
                # If color-specific, only unset primary for this color
                ProductImage.objects.filter(
                    product=self.product,
                    color=self.color,
                    is_primary=True
                ).exclude(pk=self.pk).update(is_primary=False)
            else:
                # If not color-specific, unset primary for all non-color images
                ProductImage.objects.filter(
                    product=self.product,
                    color__isnull=True,
                    is_primary=True
                ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductHighlight(models.Model):
    """
    Product highlights (bullet points)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='highlights')
    text = models.CharField(max_length=255)
    display_order = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order']
    
    def __str__(self):
        return f"{self.product.name} - {self.text[:30]}"


class ProductSpecification(models.Model):
    """
    Product specifications/details
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    title = models.CharField(max_length=100)
    value = models.CharField(max_length=255)
    display_order = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order']
    
    def __str__(self):
        return f"{self.product.name} - {self.title}"