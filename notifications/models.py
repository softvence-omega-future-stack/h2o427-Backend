from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class FCMDevice(models.Model):
    """Store FCM device tokens for push notifications"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_devices')
    registration_token = models.CharField(max_length=255, unique=True)
    device_type = models.CharField(
        max_length=10,
        choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')],
        default='web'
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'registration_token']
    
    def __str__(self):
        return f"{self.user.username} - {self.device_type}"


class Notification(models.Model):
    """
    Notification model for bidirectional communication between admin and users
    """
    # Notification types
    ADMIN_TO_USER = 'admin_to_user'
    USER_TO_ADMIN = 'user_to_admin'
    SYSTEM = 'system'
    
    TYPE_CHOICES = [
        (ADMIN_TO_USER, 'Admin to User'),
        (USER_TO_ADMIN, 'User to Admin'),
        (SYSTEM, 'System'),
    ]
    
    # Notification categories
    BACKGROUND_CHECK = 'background_check'
    SUBSCRIPTION = 'subscription'
    PAYMENT = 'payment'
    REPORT = 'report'
    GENERAL = 'general'
    
    CATEGORY_CHOICES = [
        (BACKGROUND_CHECK, 'Background Check'),
        (SUBSCRIPTION, 'Subscription'),
        (PAYMENT, 'Payment'),
        (REPORT, 'Report'),
        (GENERAL, 'General'),
    ]
    
    # Core fields
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text='User who receives this notification'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_notifications',
        help_text='User who sent this notification (null for system notifications)'
    )
    
    type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=ADMIN_TO_USER,
        help_text='Type of notification'
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default=GENERAL,
        help_text='Category of notification'
    )
    
    # Content
    title = models.CharField(max_length=255, help_text='Notification title')
    message = models.TextField(help_text='Notification message')
    
    # Metadata
    is_read = models.BooleanField(default=False, help_text='Whether the notification has been read')
    read_at = models.DateTimeField(null=True, blank=True, help_text='When the notification was read')
    
    # Optional related object reference
    related_object_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='Type of related object (e.g., Request, Report, Subscription)'
    )
    related_object_id = models.IntegerField(
        blank=True,
        null=True,
        help_text='ID of the related object'
    )
    
    # Optional action URL
    action_url = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text='URL for action button in notification'
    )
    
    # Push notification tracking
    push_sent = models.BooleanField(default=False, help_text='Whether push notification was sent')
    push_sent_at = models.DateTimeField(null=True, blank=True, help_text='When push notification was sent')
    push_error = models.TextField(blank=True, null=True, help_text='Error message if push failed')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['type', '-created_at']),
            models.Index(fields=['category', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_type_display()}: {self.title} - {self.recipient.username}"
    
    def mark_as_read(self):
        """Mark this notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
    
    def mark_as_unread(self):
        """Mark this notification as unread"""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])
