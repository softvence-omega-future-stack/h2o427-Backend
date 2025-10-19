from django.urls import path, include
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Subscription plan management
    path('plans/', views.SubscriptionPlansView.as_view(), name='subscription-plans'),
    
    # User subscription management
    path('subscription/', views.UserSubscriptionView.as_view(), name='user-subscription'),
    path('subscription/usage/', views.SubscriptionUsageView.as_view(), name='subscription-usage'),
    
    # Payment management
    path('payments/', views.PaymentHistoryView.as_view(), name='payment-history'),
    
    # Stripe webhooks
    path('webhooks/stripe/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # Admin statistics
    path('admin/stats/', views.AdminSubscriptionStatsView.as_view(), name='admin-subscription-stats'),
]
