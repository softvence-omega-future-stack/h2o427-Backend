from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class SubscriptionPlan(models.Model):
    PLAN_TYPES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='basic')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    billing_cycle = models.CharField(max_length=10, choices=BILLING_CYCLES, default='monthly')
    description = models.TextField()
    
    # Feature limits
    max_requests_per_month = models.IntegerField(default=5)
    priority_support = models.BooleanField(default=False)
    advanced_reports = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    bulk_requests = models.BooleanField(default=False)
    
    # Verification features
    basic_identity_verification = models.BooleanField(default=True)
    criminal_records_search = models.BooleanField(default=True)
    employment_verification = models.BooleanField(default=False)
    education_verification = models.BooleanField(default=False)
    federal_records_search = models.BooleanField(default=False)
    
    # Stripe integration
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.name} - ${self.price}/{self.billing_cycle}"
    
    def has_feature(self, feature_name):
        """Check if this plan has a specific feature"""
        try:
            return PlanFeature.objects.filter(
                plan=self, 
                feature__name=feature_name
            ).exists()
        except:
            return False
        
# Subscription Status Choices
class UserSubscription(models.Model):
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('canceled', 'Canceled'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('trialing', 'Trialing'),
    ]
    
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey('SubscriptionPlan', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Stripe integration
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Subscription details
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='inactive')
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end = models.DateTimeField(null=True, blank=True)
    
    # Usage tracking
    requests_used_this_month = models.IntegerField(default=0)
    last_reset_date = models.DateTimeField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'}"
    
    @property
    def is_active(self):
        """Check if subscription is currently active"""
        if self.status == 'active':
            if self.end_date and self.end_date < timezone.now():
                return False
            return True
        return False
    
    @property
    def can_make_request(self):
        """Check if user can make a new request based on their plan limits"""
        if not self.is_active or not self.plan:
            return False
        
        # Reset monthly usage if needed
        self.reset_monthly_usage_if_needed()
        
        return self.requests_used_this_month < self.plan.max_requests_per_month
    
    @property
    def remaining_requests(self):
        """Get remaining requests for current month"""
        if not self.plan:
            return 0
        
        self.reset_monthly_usage_if_needed()
        return max(0, self.plan.max_requests_per_month - self.requests_used_this_month)
    
    def reset_monthly_usage_if_needed(self):
        """Reset monthly usage if a new month has started"""
        now = timezone.now()
        if self.last_reset_date.month != now.month or self.last_reset_date.year != now.year:
            self.requests_used_this_month = 0
            self.last_reset_date = now
            self.save()
    
    def increment_usage(self):
        """Increment the request usage counter"""
        self.requests_used_this_month += 1
        self.save()


class PaymentHistory(models.Model):
    PAYMENT_STATUS = [
        ('succeeded', 'Succeeded'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS)
    
    # Stripe integration
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Additional info
    description = models.TextField(blank=True)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - ${self.amount} ({self.status})"

class SubscriptionFeature(models.Model):
    """Model to track individual features and their availability per plan"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    feature_key = models.CharField(max_length=50, unique=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.feature_key:
            self.feature_key = self.name.lower().replace(' ', '_')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class PlanFeature(models.Model):
    """Junction table to connect plans with features"""
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='features')
    feature = models.ForeignKey(SubscriptionFeature, on_delete=models.CASCADE)
    is_included = models.BooleanField(default=True)
    limit_value = models.IntegerField(null=True, blank=True)  # For features with limits
    
    class Meta:
        unique_together = ['plan', 'feature']

    def __str__(self):
        return f"{self.plan.name} - {self.feature.name}"
