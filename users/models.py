from django.db import models
from django.contrib.auth.models import AbstractUser
from django.urls import reverse

class User(AbstractUser):
    email = models.EmailField(unique=True, null=True, blank=False)  # Thêm null=True để tránh lỗi migration
    is_seller = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.username
    
    def get_absolute_url(self):
        return reverse('users:profile', kwargs={'pk': self.pk})


class SellerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    shop_name = models.CharField(max_length=100)
    shop_description = models.TextField(blank=True, null=True)
    shop_logo = models.ImageField(upload_to='shop_logos/', blank=True, null=True)

    def __str__(self):
        return f"{self.shop_name} - {self.user.username}"
    
    def get_absolute_url(self):
        return reverse('users:seller_profile', kwargs={'pk': self.pk})


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    recipient_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    street_address = models.CharField(max_length=255)
    ward = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural = "Addresses"
        
    def __str__(self):
        return f"{self.recipient_name}, {self.street_address}, {self.district}, {self.city}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other addresses of this user to non-default
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)