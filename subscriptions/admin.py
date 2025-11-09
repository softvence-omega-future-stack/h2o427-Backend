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
        'name', 'plan_type', 'price_display', 
        'subscriber_count', 'is_active', 'created_at'
    ]
    list_filter = ['plan_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'subscriber_count', 'revenue_generated']
    ordering = ['price_per_report']
    
    def price_display(self, obj):
        """Format price with currency"""
        return format_html("$<span>{}</span> per report", obj.price_per_report)
    price_display.short_description = "Price"
    price_display.admin_order_field = 'price_per_report'
    
    def subscriber_count(self, obj):
        """Count of subscribers using this plan"""
        return UserSubscription.objects.filter(plan=obj).count()
    subscriber_count.short_description = "Subscribers"
    
    def revenue_generated(self, obj):
        """Calculate total revenue from this plan"""
        total_revenue = PaymentHistory.objects.filter(
            plan=obj,
            status='succeeded'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        return format_html("$<span>{}</span>", f"{total_revenue:.2f}")
    revenue_generated.short_description = "Total Revenue"
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'plan_type', 'description')
        }),
        ('Pricing', {
            'fields': ('price_per_report',)
        }),
        ('Basic Features', {
            'fields': (
                'identity_verification', 'ssn_trace',
                'national_criminal_search', 'sex_offender_registry'
            )
        }),
        ('Premium Features', {
            'fields': (
                'employment_verification', 'education_verification', 
                'unlimited_county_search'
            ),
            'classes': ('collapse',)
        }),
        ('Support & Access', {
            'fields': ('priority_support', 'api_access'),
            'classes': ('collapse',)
        }),
        ('Stripe Integration', {
            'fields': ('stripe_price_id', 'stripe_product_id'),
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
        'user_link', 'plan_link', 'available_reports_display',
        'free_trial_status', 'created_at'
    ]
    list_filter = ['plan__plan_type', 'free_trial_used', 'created_at']
    search_fields = [
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
        'plan__name', 'stripe_customer_id'
    ]
    readonly_fields = [
        'created_at', 'updated_at', 'can_make_request_display',
        'total_payments'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def user_link(self, obj):
        """Link to user admin page"""
        try:
            pattern_name = f"admin:{obj.user._meta.app_label}_{obj.user._meta.model_name}_change"
            url = reverse(pattern_name, args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        except Exception as e:
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
    
    def available_reports_display(self, obj):
        """Show available reports"""
        available = obj.available_reports
        color = 'green' if available > 0 else 'red'
        return format_html(
            '<span style="color: {};">{} available</span> ({} used / {} purchased)',
            color, available, obj.total_reports_used, obj.total_reports_purchased
        )
    available_reports_display.short_description = "Reports"
    
    def free_trial_status(self, obj):
        """Show free trial status"""
        if obj.free_trial_used:
            if obj.free_trial_date:
                return format_html('<span style="color: orange;">Used on {}</span>', obj.free_trial_date.strftime('%Y-%m-%d'))
            return format_html('<span style="color: orange;">Used</span>')
        return format_html('<span style="color: green;">Available</span>')
    free_trial_status.short_description = "Free Trial"
    
    def can_make_request_display(self, obj):
        """Show if user can make requests"""
        if obj.can_make_request:
            return format_html('<span style="color: green;">Yes</span>')
        return format_html('<span style="color: red;">No</span>')
    can_make_request_display.short_description = "Can Make Request"
    
    def total_payments(self, obj):
        """Calculate total payments for this user"""
        total = PaymentHistory.objects.filter(
            user=obj.user,
            status='succeeded'
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        return format_html("$<span>{}</span>", f"{total:.2f}")
    total_payments.short_description = "Total Payments"
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'plan')
        }),
        ('Free Trial', {
            'fields': ('free_trial_used', 'free_trial_date')
        }),
        ('Usage Tracking', {
            'fields': (
                'total_reports_purchased', 'total_reports_used', 
                'can_make_request_display'
            )
        }),
        ('Stripe Integration', {
            'fields': ('stripe_customer_id',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'total_payments'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['reset_usage', 'reset_free_trial', 'add_report_credits']
    
    def reset_usage(self, request, queryset):
        """Reset usage counter for selected subscriptions"""
        count = 0
        for subscription in queryset:
            subscription.total_reports_used = 0
            subscription.save()
            count += 1
        self.message_user(request, f"Reset usage for {count} subscriptions.")
    reset_usage.short_description = "Reset usage counter"
    
    def reset_free_trial(self, request, queryset):
        """Reset free trial for selected subscriptions"""
        count = queryset.update(free_trial_used=False, free_trial_date=None)
        self.message_user(request, f"Reset free trial for {count} subscriptions.")
    reset_free_trial.short_description = "Reset free trial"
    
    def add_report_credits(self, request, queryset):
        """Add 1 report credit to selected subscriptions"""
        count = 0
        for subscription in queryset:
            subscription.total_reports_purchased += 1
            subscription.save()
            count += 1
        self.message_user(request, f"Added 1 report credit to {count} subscriptions.")
    add_report_credits.short_description = "Add 1 report credit"


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    """Admin interface for payment history"""
    list_display = [
        'user_link', 'amount_display', 'reports_purchased', 'plan_link',
        'currency', 'status_badge', 'created_at'
    ]
    list_filter = ['status', 'currency', 'created_at', 'plan__plan_type']
    search_fields = [
        'user__username', 'user__email', 'plan__name',
        'stripe_payment_intent_id', 'stripe_charge_id', 'description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    def user_link(self, obj):
        """Link to user admin page"""
        try:
            pattern_name = f"admin:{obj.user._meta.app_label}_{obj.user._meta.model_name}_change"
            url = reverse(pattern_name, args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        except Exception as e:
            return obj.user.username
    user_link.short_description = "User"
    user_link.admin_order_field = 'user__username'
    
    def plan_link(self, obj):
        """Link to plan admin page"""
        if obj.plan:
            url = reverse("admin:subscriptions_subscriptionplan_change", args=[obj.plan.pk])
            return format_html('<a href="{}">{}</a>', url, obj.plan.name)
        return "N/A"
    plan_link.short_description = "Plan"
    
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
            'refunded': 'blue',
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
            'fields': ('user', 'subscription', 'plan', 'amount', 'reports_purchased', 'currency', 'status')
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
