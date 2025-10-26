from django.urls import path, include
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # API endpoints
    path('plans/', views.SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('', views.UserSubscriptionView.as_view(), name='user-subscription'),  # GET, POST, PATCH, DELETE /api/subscriptions/
    path('subscription/', views.UserSubscriptionView.as_view(), name='user-subscription-alt'),  # Alternative path
    path('usage/', views.SubscriptionUsageView.as_view(), name='subscription-usage'),
    path('create-checkout-session/', views.CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('verify-checkout-session/', views.VerifyCheckoutSessionView.as_view(), name='verify-checkout-session'),
    path('payment-history/', views.PaymentHistoryView.as_view(), name='payment-history'),
    path('webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    path('admin/stats/', views.AdminSubscriptionStatsView.as_view(), name='admin-subscription-stats'),
    
    # Template-based views (MVT)
    path('ui/plans/', views.plans_list_view, name='plans_list'),
    path('ui/subscribe/', views.subscribe_plan_view, name='subscribe_plan'),
    path('ui/success/', views.subscription_success_view, name='subscription_success'),
    path('ui/cancel/', views.subscription_cancel_view, name='subscription_cancel'),
    path('ui/dashboard/', views.subscription_dashboard_view, name='subscription_dashboard'),
]
        