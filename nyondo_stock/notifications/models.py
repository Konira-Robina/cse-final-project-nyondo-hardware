from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Notification(models.Model):

    CATEGORY_CHOICES = [
        ('low_stock', 'Low Stock'),
        ('overdue_credit', 'Overdue Supplier Credit'),
        ('deposit_ready', 'Deposit Ready for Pickup'),
        ('new_sale', 'New Sale'),
        ('new_delivery', 'New Delivery'),
        ('credit_payment', 'Credit Payment Made'),
        ('new_deposit', 'New Deposit'),
    ]

    LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
        ('success', 'Success'),
    ]

    TARGET_ROLE_CHOICES = [
        ('all', 'All Staff'),
        ('admin', 'Accounts / Admin'),
        ('store_manager', 'Store Manager'),
        ('sales_attendant', 'Sales Attendant'),
    ]

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text='Leave blank to target by role instead'
    )
    target_role = models.CharField(
        max_length=20,
        choices=TARGET_ROLE_CHOICES,
        default='all',
        help_text='Used when recipient is blank'
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='info')
    title = models.CharField(max_length=200)
    message = models.TextField()
    link = models.CharField(max_length=200, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.level.upper()}] {self.title}"

    @classmethod
    def notify(cls, category, title, message,
               level='info', link='', target_role='all', recipient=None):
        """
        Central method to create a notification.
        Call this from anywhere in the project.
        """
        cls.objects.create(
            category=category,
            title=title,
            message=message,
            level=level,
            link=link,
            target_role=target_role,
            recipient=recipient,
        )

    @classmethod
    def mark_all_read(cls, user):
        """Mark all notifications visible to this user as read."""
        from accounts.models import UserProfile
        try:
            role = user.profile.role
        except UserProfile.DoesNotExist:
            role = None

        cls.objects.filter(
            is_read=False
        ).filter(
            models.Q(recipient=user) |
            models.Q(target_role='all') |
            models.Q(target_role=role)
        ).update(is_read=True)

    @classmethod
    def for_user(cls, user):
        """Return all notifications visible to this user."""
        from accounts.models import UserProfile
        try:
            role = user.profile.role
        except UserProfile.DoesNotExist:
            role = None

        return cls.objects.filter(
            models.Q(recipient=user) |
            models.Q(target_role='all') |
            models.Q(target_role=role)
        ).order_by('-created_at')

    @classmethod
    def unread_count(cls, user):
        return cls.for_user(user).filter(is_read=False).count()