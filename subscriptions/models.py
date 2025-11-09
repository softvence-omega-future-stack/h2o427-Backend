from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class SubscriptionPlan(models.Model):
    """Model for per-report subscription plans"""
    PLAN_TYPES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
    ]
    
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='basic')
    price_per_report = models.DecimalField(max_digits=10, decimal_places=2, default=25.00, help_text="Price charged per background check report")
    description = models.TextField()
    
    # Features - Basic Plan
    identity_verification = models.BooleanField(default=False, help_text="Identity Verification")
    ssn_trace = models.BooleanField(default=False, help_text="SSN Trace")
    national_criminal_search = models.BooleanField(default=False, help_text="National Criminal Search")
    sex_offender_registry = models.BooleanField(default=False, help_text="Sex Offender Registry")
    
    # Features - Premium Plan (includes all Basic)
    employment_verification = models.BooleanField(default=False, help_text="Employment History")
    education_verification = models.BooleanField(default=False, help_text="Education Verification")
    unlimited_county_search = models.BooleanField(default=False, help_text="Unlimited County Criminal Search")
    
    # Support and Access
    priority_support = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    
    # Stripe integration
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price_per_report']

    def __str__(self):
        return f"{self.name} - ${self.price_per_report} per report"
    
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
    """User's subscription for per-report purchases"""
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey('SubscriptionPlan', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Stripe integration (for payment processing)
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Free trial tracking
    free_trial_used = models.BooleanField(default=False, help_text="Has the user used their 1 free search trial")
    free_trial_date = models.DateTimeField(null=True, blank=True, help_text="When the free trial was used")
    
    # Usage tracking (total reports purchased, not monthly)
    total_reports_purchased = models.IntegerField(default=0, help_text="Total number of reports user has purchased")
    total_reports_used = models.IntegerField(default=0, help_text="Total number of reports user has used")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'No Plan'}"
    
    @property
    def can_use_free_trial(self):
        """Check if user can use their free trial search"""
        return not self.free_trial_used
    
    def use_free_trial(self):
        """Mark free trial as used"""
        if not self.free_trial_used:
            self.free_trial_used = True
            self.free_trial_date = timezone.now()
            self.save()
            return True
        return False
    
    @property
    def available_reports(self):
        """Get number of reports available to use"""
        return self.total_reports_purchased - self.total_reports_used
    
    @property
    def can_make_request(self):
        """Check if user can make a new request (has free trial or purchased reports)"""
        return self.can_use_free_trial or self.available_reports > 0
    
    def increment_usage(self):
        """Increment the report usage counter"""
        if self.can_use_free_trial:
            self.use_free_trial()
        elif self.available_reports > 0:
            self.total_reports_used += 1
            self.save()
        else:
            raise ValueError("No reports available. Please purchase more reports.")




class PaymentHistory(models.Model):
    """Track all per-report purchase payments"""
    PAYMENT_STATUS = [
        ('succeeded', 'Succeeded'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, help_text="Which plan was used for this purchase")
    
    # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount paid for the report")
    reports_purchased = models.IntegerField(default=1, help_text="Number of reports purchased in this transaction")
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
        verbose_name_plural = 'Payment Histories'

    def __str__(self):
        return f"{self.user.username} - ${self.amount} ({self.reports_purchased} report{'s' if self.reports_purchased > 1 else ''}) - {self.status}"

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
