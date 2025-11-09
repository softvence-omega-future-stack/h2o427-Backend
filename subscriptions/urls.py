from django.urls import path, include
from . import views
from .page_views import plans_page, select_plan, purchase_page, my_dashboard

app_name = 'subscriptions'

urlpatterns = [
    # API endpoints
    path('plans/', views.SubscriptionPlansView.as_view(), name='subscription-plans'),
    path('', views.UserSubscriptionView.as_view(), name='user-subscription'),  # GET, POST, PATCH, DELETE /api/subscriptions/
    path('subscription/', views.UserSubscriptionView.as_view(), name='user-subscription-alt'),  # Alternative path
    path('usage/', views.SubscriptionUsageView.as_view(), name='subscription-usage'),
    path('payment-history/', views.PaymentHistoryView.as_view(), name='payment-history'),
    
    # Per-Report Purchase endpoints
    path('purchase-report/', views.PurchaseReportView.as_view(), name='purchase-report'),
    path('confirm-payment/', views.ConfirmPaymentView.as_view(), name='confirm-payment'),
    path('purchase-cancelled/', views.PurchaseCancelledView.as_view(), name='purchase-cancelled'),
    path('test-purchase/', views.TestPurchaseReportsView.as_view(), name='test-purchase'),  # TEST ONLY - No Stripe
    
    # Stripe integration
    path('create-checkout-session/', views.CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('verify-checkout-session/', views.VerifyCheckoutSessionView.as_view(), name='verify-checkout-session'),
    path('webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # Admin
    path('admin/stats/', views.AdminSubscriptionStatsView.as_view(), name='admin-subscription-stats'),
    
    # Template-based views (MVT)
    path('ui/plans/', views.plans_list_view, name='plans_list'),
    path('ui/subscribe/', views.subscribe_plan_view, name='subscribe_plan'),
    path('ui/success/', views.subscription_success_view, name='subscription_success'),
    path('ui/cancel/', views.subscription_cancel_view, name='subscription_cancel'),
    path('ui/dashboard/', views.subscription_dashboard_view, name='subscription_dashboard'),
    
    # New simple UI template views
    path('plans-page/', plans_page, name='plans-page'),
    path('select-plan/', select_plan, name='select-plan'),
    path('purchase-page/', purchase_page, name='purchase-page'),
    path('my-dashboard/', my_dashboard, name='my-dashboard'),
]
        