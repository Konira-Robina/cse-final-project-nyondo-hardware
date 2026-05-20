from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('sales_attendant', 'Sales Attendant'),
        ('store_manager', 'Store Manager'),
        ('admin', 'Accounts / Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.get_role_display()}"
