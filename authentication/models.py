from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    full_name = models.CharField(max_length=255, blank=True, null=True, help_text="User's full name")
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True, db_index=True, help_text='International phone number, e.g. +15551234567')
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, help_text="User's profile picture")
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, help_text='Stripe customer ID')
    
    # Override email to make it required
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return self.username or self.email


class PhoneOTP(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='otps',
        blank=True,
        null=True
    )
    phone_number = models.CharField(max_length=20, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Set expiration time from settings or default to 5 minutes
            ttl_seconds = getattr(settings, 'PHONE_OTP_TTL_SECONDS', 300)
            self.expires_at = timezone.now() + timedelta(seconds=ttl_seconds)
        super().save(*args, **kwargs)

    def is_otp_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"OTP for {self.phone_number} - {'Verified' if self.verified else 'Pending'}"
