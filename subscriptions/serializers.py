from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SubscriptionPlan, UserSubscription, PaymentHistory, SubscriptionFeature, PlanFeature

User = get_user_model()

class SubscriptionFeatureSerializer(serializers.ModelSerializer):
    """Serializer for individual subscription features"""
    class Meta:
        model = SubscriptionFeature
        fields = ['id', 'name', 'description', 'feature_key', 'is_active']

class PlanFeatureSerializer(serializers.ModelSerializer):
    """Serializer for plan-feature relationships"""
    feature = SubscriptionFeatureSerializer(read_only=True)
    
    class Meta:
        model = PlanFeature
        fields = ['feature', 'is_included', 'limit_value']

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for subscription plans"""
    features = PlanFeatureSerializer(many=True, read_only=True)
    feature_list = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'plan_type', 'price', 'billing_cycle', 'description',
            'max_requests_per_month', 'priority_support', 'advanced_reports', 
            'api_access', 'bulk_requests', 'basic_identity_verification',
            'criminal_records_search', 'employment_verification', 
            'education_verification', 'federal_records_search',
            'stripe_price_id', 'is_active', 'features', 'feature_list'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_feature_list(self, obj):
        """Get a simplified list of included features"""
        features = []
        
        # Add built-in features
        if obj.basic_identity_verification:
            features.append("Basic identity verification")
        if obj.criminal_records_search and not obj.federal_records_search:
            features.append("County criminal records search")
        if obj.federal_records_search:
            features.append("Federal, state & county criminal records")
        if obj.employment_verification:
            features.append("Employment history verification")
        if obj.education_verification:
            features.append("Education verification")
        if obj.priority_support:
            features.append("Priority Support")
        if obj.advanced_reports:
            features.append("30-day report access")
        if obj.api_access:
            features.append("API Access")
        if obj.bulk_requests:
            features.append("Bulk requests")
        
        # Add request limit
        if obj.max_requests_per_month > 900000:
            features.append("Unlimited requests")
        else:
            features.append(f"Up to {obj.max_requests_per_month} requests per month")
        
        # Add support level
        if not obj.priority_support:
            features.append("Standard support")
        
        return features

class UserSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for user subscriptions"""
    plan = SubscriptionPlanSerializer(read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    user_name = serializers.CharField(source='user.username', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    can_make_request = serializers.BooleanField(read_only=True)
    remaining_requests = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'user', 'user_name', 'plan', 'plan_name', 'status', 
            'start_date', 'end_date', 'trial_end', 'requests_used_this_month',
            'last_reset_date', 'is_active', 'can_make_request', 'remaining_requests',
            'stripe_subscription_id', 'stripe_customer_id', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'requests_used_this_month', 'last_reset_date',
            'is_active', 'can_make_request', 'remaining_requests', 'created_at', 'updated_at'
        ]

class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for payment history"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    subscription_plan = serializers.CharField(source='subscription.plan.name', read_only=True)
    
    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'user', 'user_name', 'subscription', 'subscription_plan',
            'amount', 'currency', 'status', 'description', 'failure_reason',
            'stripe_payment_intent_id', 'stripe_charge_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CreateSubscriptionSerializer(serializers.Serializer):
    """Serializer for creating a new subscription"""
    plan_id = serializers.IntegerField()
    payment_method_id = serializers.CharField(max_length=255, required=False)
    trial_period_days = serializers.IntegerField(default=0, min_value=0, max_value=30)
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive subscription plan.")

class UpdateSubscriptionSerializer(serializers.Serializer):
    """Serializer for updating subscription plan"""
    plan_id = serializers.IntegerField()
    prorate = serializers.BooleanField(default=True)
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid or inactive subscription plan.")

class CancelSubscriptionSerializer(serializers.Serializer):
    """Serializer for canceling subscription"""
    cancel_at_period_end = serializers.BooleanField(default=True)
    cancellation_reason = serializers.CharField(max_length=500, required=False, allow_blank=True)

class SubscriptionUsageSerializer(serializers.Serializer):
    """Serializer for subscription usage information"""
    current_plan = SubscriptionPlanSerializer(read_only=True)
    requests_used_this_month = serializers.IntegerField(read_only=True)
    requests_remaining = serializers.IntegerField(read_only=True)
    max_requests_per_month = serializers.IntegerField(read_only=True)
    usage_percentage = serializers.SerializerMethodField()
    can_make_request = serializers.BooleanField(read_only=True)
    subscription_status = serializers.CharField(read_only=True)
    next_billing_date = serializers.DateTimeField(read_only=True)
    
    def get_usage_percentage(self, obj):
        """Calculate usage percentage"""
        if obj.get('max_requests_per_month', 0) > 0:
            return round((obj.get('requests_used_this_month', 0) / obj.get('max_requests_per_month', 1)) * 100, 2)
        return 0

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