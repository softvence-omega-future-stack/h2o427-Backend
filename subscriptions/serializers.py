from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SubscriptionPlan, UserSubscription, PaymentHistory

User = get_user_model()

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans - Per-Report Pricing"""
    feature_list = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'plan_type', 'price_per_report', 'description',
            'identity_verification', 'ssn_trace', 'national_criminal_search',
            'sex_offender_registry', 'employment_verification', 
            'education_verification', 'unlimited_county_search',
            'priority_support', 'api_access',
            'stripe_price_id', 'stripe_product_id', 'is_active', 'feature_list',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_feature_list(self, obj):
        """Get a simplified list of included features"""
        features = []
        
        # Basic features
        if obj.identity_verification:
            features.append("Identity Verification")
        if obj.ssn_trace:
            features.append("SSN Trace")
        if obj.national_criminal_search:
            features.append("National Criminal Search")
        if obj.sex_offender_registry:
            features.append("Sex Offender Registry")
        
        # Premium features
        if obj.employment_verification:
            features.append("Employment History Verification")
        if obj.education_verification:
            features.append("Education Verification")
        if obj.unlimited_county_search:
            features.append("Unlimited County Criminal Search")
        
        # Support
        if obj.priority_support:
            features.append("Priority Support")
        else:
            features.append("Standard Support")
        
        if obj.api_access:
            features.append("API Access")
        
        return features

class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions - Per-Report Pricing"""
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    can_make_request = serializers.BooleanField(read_only=True)
    available_reports = serializers.IntegerField(read_only=True)
    can_use_free_trial = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user', 'user_name', 'plan', 'plan_name',
            'free_trial_used', 'free_trial_date',
            'total_reports_purchased', 'total_reports_used', 'available_reports',
            'can_make_request', 'can_use_free_trial',
            'stripe_customer_id', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'free_trial_date', 'total_reports_used',
            'can_make_request', 'available_reports', 'can_use_free_trial',
            'created_at', 'updated_at'
        ]

class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for payment history - Per-Report Pricing"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    
    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'user', 'user_name', 'subscription', 'plan', 'plan_name',
            'amount', 'reports_purchased', 'currency', 'status', 
            'description', 'failure_reason',
            'stripe_payment_intent_id', 'stripe_charge_id', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CreateSubscriptionSerializer(serializers.Serializer):
    """Serializer for selecting a plan (not creating subscription)"""
    plan_id = serializers.IntegerField()
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive subscription plan.")


class PurchaseReportSerializer(serializers.Serializer):
    """Serializer for purchasing reports"""
    plan_id = serializers.IntegerField()
    quantity = serializers.IntegerField(default=1, min_value=1, max_value=100)
    payment_method_id = serializers.CharField(max_length=255, required=False)
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive subscription plan.")

class UpdateSubscriptionSerializer(serializers.Serializer):
    """Serializer for changing subscription plan"""
    plan_id = serializers.IntegerField()
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive subscription plan.")


class CancelSubscriptionSerializer(serializers.Serializer):
    """Serializer for canceling subscription"""
    cancellation_reason = serializers.CharField(max_length=500, required=False, allow_blank=True)

class SubscriptionUsageSerializer(serializers.Serializer):
    """Serializer for subscription usage information - Per-Report Pricing"""
    current_plan = SubscriptionPlanSerializer(read_only=True)
    total_reports_purchased = serializers.IntegerField(read_only=True)
    total_reports_used = serializers.IntegerField(read_only=True)
    available_reports = serializers.IntegerField(read_only=True)
    free_trial_used = serializers.BooleanField(read_only=True)
    can_use_free_trial = serializers.BooleanField(read_only=True)
    can_make_request = serializers.BooleanField(read_only=True)

class SubscriptionStatsSerializer(serializers.Serializer):
    """Serializer for subscription statistics (admin use)"""
    total_subscribers = serializers.IntegerField()
    active_subscribers = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    most_popular_plan = SubscriptionPlanSerializer()
    recent_payments = PaymentHistorySerializer(many=True)
    
class StripeCustomerSerializer(serializers.Serializer):
    """Serializer for Stripe customer creation"""
    email = serializers.EmailField()
    name = serializers.CharField(max_length=255)
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.DictField(required=False)