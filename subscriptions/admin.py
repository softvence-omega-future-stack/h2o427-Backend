from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db import models
from .models import (
    SubscriptionPlan, 
    UserSubscription, 
    PaymentHistory, 
    SubscriptionFeature, 
    PlanFeature
)


class PlanFeatureInline(admin.TabularInline):
    """Inline admin for managing plan features"""
    model = PlanFeature
    extra = 1
    verbose_name = "Feature"
    verbose_name_plural = "Plan Features"


@admin.register(SubscriptionFeature)
class SubscriptionFeatureAdmin(admin.ModelAdmin):
    """Admin interface for subscription features"""
    list_display = ['name', 'feature_key', 'description_preview', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'feature_key', 'description']
    readonly_fields = ['feature_key', 'created_at']
    ordering = ['name']
    
    def description_preview(self, obj):
        """Show truncated description"""
        if len(obj.description) > 50:
            return obj.description[:50] + "..."
        return obj.description
    description_preview.short_description = "Description"
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'feature_key', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Admin interface for subscription plans"""
    list_display = [
        'name', 'plan_type', 'price_display', 'billing_cycle', 
        'max_requests_per_month', 'feature_count', 'subscriber_count', 
        'is_active', 'created_at'
    ]
    list_filter = ['plan_type', 'billing_cycle', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'subscriber_count', 'revenue_generated']
    ordering = ['price']
    inlines = [PlanFeatureInline]
    
    def price_display(self, obj):
        """Format price with currency"""
        return format_html("$<span>{}</span>", obj.price)
    price_display.short_description = "Price"
    price_display.admin_order_field = 'price'
    
    def feature_count(self, obj):
        """Count of features in this plan"""
        return obj.features.count()
    feature_count.short_description = "Features"
    
    def subscriber_count(self, obj):
        """Count of active subscribers"""
        return UserSubscription.objects.filter(plan=obj, status='active').count()
    subscriber_count.short_description = "Active Subscribers"
    
    def revenue_generated(self, obj):
        """Calculate total revenue from this plan"""
        total_revenue = PaymentHistory.objects.filter(
            subscription__plan=obj,
            status='succeeded'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        return format_html("$<span>{}</span>", f"{total_revenue:.2f}")
    revenue_generated.short_description = "Total Revenue"
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'plan_type', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'billing_cycle')
        }),
        ('Limits & Features', {
            'fields': (
                'max_requests_per_month', 'priority_support', 
                'advanced_reports', 'api_access', 'bulk_requests'
            )
        }),
        ('Verification Features', {
            'fields': (
                'basic_identity_verification', 'criminal_records_search',
                'employment_verification', 'education_verification', 
                'federal_records_search'
            ),
            'classes': ('collapse',)
        }),
        ('Stripe Integration', {
            'fields': ('stripe_price_id',),
            'classes': ('collapse',)
        }),
        ('Status & Metadata', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('subscriber_count', 'revenue_generated'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    """Admin interface for user subscriptions"""
    list_display = [
        'user_link', 'plan_link', 'status_badge', 'requests_used_display',
        'start_date', 'end_date', 'created_at'
    ]
    list_filter = ['status', 'plan__plan_type', 'start_date', 'end_date', 'created_at']
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'plan__name', 'stripe_customer_id', 'stripe_subscription_id'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'remaining_requests', 'can_make_request_display',
        'subscription_age', 'total_payments'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def user_link(self, obj):
        """Link to user admin page"""
        try:
            # First construct the URL pattern name
            pattern_name = f"admin:{obj.user._meta.app_label}_{obj.user._meta.model_name}_change"
            url = reverse(pattern_name, args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        except Exception as e:
            # If that fails, just return the username without a link
            return obj.user.username
    user_link.short_description = "User"
    user_link.admin_order_field = 'user__username'
    
    def plan_link(self, obj):
        """Link to plan admin page"""
        if obj.plan:
            url = reverse("admin:subscriptions_subscriptionplan_change", args=[obj.plan.pk])
            return format_html('<a href="{}">{}</a>', url, obj.plan.name)
        return "No Plan"
    plan_link.short_description = "Plan"
    plan_link.admin_order_field = 'plan__name'
    
    def status_badge(self, obj):
        """Colored status badge"""
        colors = {
            'active': 'green',
            'canceled': 'red',
            'incomplete': 'orange',
            'past_due': 'red',
            'unpaid': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = 'status'
    
    def requests_used_display(self, obj):
        """Show usage with progress bar"""
        if obj.plan and obj.plan.max_requests_per_month > 0 and obj.plan.max_requests_per_month < 900000:
            percentage = (obj.requests_used_this_month / obj.plan.max_requests_per_month) * 100
            color = 'green' if percentage < 80 else 'orange' if percentage < 100 else 'red'
            return format_html(
                '{}/{} <span style="color: {};">({}%)</span>',
                obj.requests_used_this_month,
                obj.plan.max_requests_per_month,
                color,
                f"{percentage:.1f}"
            )
        elif obj.plan:
            # For unlimited plans
            return format_html("<span>{} / Unlimited</span>", obj.requests_used_this_month)
        else:
            # No plan assigned
            return format_html("<span>{} / No Plan</span>", obj.requests_used_this_month)
    requests_used_display.short_description = "Requests Used"
    
    def remaining_requests(self, obj):
        """Calculate remaining requests"""
        return obj.remaining_requests
    remaining_requests.short_description = "Remaining Requests"
    
    def can_make_request_display(self, obj):
        """Show if user can make requests"""
        if obj.can_make_request:
            return format_html('<span style="color: green;">✓ Yes</span>')
        return format_html('<span style="color: red;">✗ No</span>')
    can_make_request_display.short_description = "Can Make Request"
    
    def subscription_age(self, obj):
        """Calculate subscription age"""
        from django.utils import timezone
        if obj.start_date:
            age = timezone.now() - obj.start_date
            return format_html("<span>{} days</span>", age.days)
        return "N/A"
    subscription_age.short_description = "Subscription Age"
    
    def total_payments(self, obj):
        """Calculate total payments for this subscription"""
        total = PaymentHistory.objects.filter(
            subscription=obj,
            status='succeeded'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        return format_html("$<span>{}</span>", f"{total:.2f}")
    total_payments.short_description = "Total Payments"
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'plan', 'status')
        }),
        ('Dates', {
            'fields': ('start_date', 'end_date', 'trial_end')
        }),
        ('Usage Tracking', {
            'fields': (
                'requests_used_this_month', 'remaining_requests', 
                'can_make_request_display'
            )
        }),
        ('Stripe Integration', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'subscription_age', 'total_payments'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reset_usage', 'activate_subscription', 'cancel_subscription']
    
    def reset_usage(self, request, queryset):
        """Reset usage counter for selected subscriptions"""
        count = 0
        for subscription in queryset:
            subscription.requests_used_this_month = 0
            subscription.save()
            count += 1
        self.message_user(request, f"Reset usage for {count} subscriptions.")
    reset_usage.short_description = "Reset usage counter"
    
    def activate_subscription(self, request, queryset):
        """Activate selected subscriptions"""
        count = queryset.update(status='active')
        self.message_user(request, f"Activated {count} subscriptions.")
    activate_subscription.short_description = "Activate subscriptions"
    
    def cancel_subscription(self, request, queryset):
        """Cancel selected subscriptions"""
        count = queryset.update(status='canceled')
        self.message_user(request, f"Canceled {count} subscriptions.")
    cancel_subscription.short_description = "Cancel subscriptions"


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    """Admin interface for payment history"""
    list_display = [
        'user_link', 'amount_display', 'currency', 'status_badge',
        'subscription_link', 'created_at'
    ]
    list_filter = ['status', 'currency', 'created_at', 'subscription__plan__plan_type']
    search_fields = [
        'user__username', 'user__email', 'subscription__plan__name',
        'stripe_payment_intent_id', 'stripe_charge_id', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def user_link(self, obj):
        """Link to user admin page"""
        try:
            # First construct the URL pattern name
            pattern_name = f"admin:{obj.user._meta.app_label}_{obj.user._meta.model_name}_change"
            url = reverse(pattern_name, args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        except Exception as e:
            # If that fails, just return the username without a link
            return obj.user.username
    user_link.short_description = "User"
    user_link.admin_order_field = 'user__username'
    
    def subscription_link(self, obj):
        """Link to subscription admin page"""
        if obj.subscription:
            url = reverse("admin:subscriptions_usersubscription_change", args=[obj.subscription.pk])
            return format_html('<a href="{}">{}</a>', url, obj.subscription.plan.name)
        return "N/A"
    subscription_link.short_description = "Subscription"
    
    def amount_display(self, obj):
        """Format amount with currency"""
        return format_html("$<span>{}</span>", f"{obj.amount:.2f}")
    amount_display.short_description = "Amount"
    amount_display.admin_order_field = 'amount'
    
    def status_badge(self, obj):
        """Colored status badge"""
        colors = {
            'succeeded': 'green',
            'failed': 'red',
            'pending': 'orange',
            'canceled': 'gray',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status.upper()
        )
    status_badge.short_description = "Status"
    status_badge.admin_order_field = 'status'
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('user', 'subscription', 'amount', 'currency', 'status')
        }),
        ('Description & Reason', {
            'fields': ('description', 'failure_reason')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_payment_intent_id', 'stripe_charge_id'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PlanFeature)
class PlanFeatureAdmin(admin.ModelAdmin):
    """Admin interface for plan-feature relationships"""
    list_display = ['plan', 'feature', 'plan_type', 'feature_active']
    list_filter = ['plan__plan_type', 'feature__is_active', 'plan__is_active']
    search_fields = ['plan__name', 'feature__name']
    ordering = ['plan__name', 'feature__name']
    
    def plan_type(self, obj):
        """Show plan type"""
        return obj.plan.plan_type
    plan_type.short_description = "Plan Type"
    
    def feature_active(self, obj):
        """Show if feature is active"""
        if obj.feature.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    feature_active.short_description = "Feature Status"


# Add custom admin site title and header
admin.site.site_header = "Background Check - Subscription Management"
admin.site.site_title = "Subscription Admin"
admin.site.index_title = "Subscription Management Dashboard"
