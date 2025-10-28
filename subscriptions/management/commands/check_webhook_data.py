"""
Django management command to check subscription and payment records
Usage: python manage.py check_webhook_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import UserSubscription, PaymentHistory, SubscriptionPlan
from authentication.models import User


class Command(BaseCommand):
    help = 'Check webhook data - subscriptions and payment history'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("  📊 Webhook Data Status"))
        self.stdout.write("="*60 + "\n")
        
        # Count records
        user_count = User.objects.count()
        plan_count = SubscriptionPlan.objects.count()
        subscription_count = UserSubscription.objects.count()
        payment_count = PaymentHistory.objects.count()
        active_subscriptions = UserSubscription.objects.filter(status='active').count()
        
        self.stdout.write(f"Users: {user_count}")
        self.stdout.write(f"Plans: {plan_count}")
        self.stdout.write(f"Total Subscriptions: {subscription_count}")
        self.stdout.write(f"Active Subscriptions: {active_subscriptions}")
        self.stdout.write(f"Payment Records: {payment_count}")
        
        # Recent subscriptions
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("  📋 Recent Subscriptions"))
        self.stdout.write("="*60 + "\n")
        
        recent_subs = UserSubscription.objects.select_related('user', 'plan').order_by('-created_at')[:10]
        
        if recent_subs:
            for sub in recent_subs:
                status_color = self.style.SUCCESS if sub.status == 'active' else self.style.WARNING
                self.stdout.write(
                    f"ID: {sub.id} | User: {sub.user.email} | "
                    f"Plan: {sub.plan.name} | "
                    f"Status: " + status_color(sub.status.upper()) + 
                    f" | Created: {sub.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
        else:
            self.stdout.write(self.style.WARNING("No subscriptions found"))
        
        # Recent payments
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("  💳 Recent Payments"))
        self.stdout.write("="*60 + "\n")
        
        recent_payments = PaymentHistory.objects.select_related('user', 'subscription').order_by('-created_at')[:10]
        
        if recent_payments:
            for payment in recent_payments:
                status_color = self.style.SUCCESS if payment.status == 'succeeded' else self.style.ERROR
                self.stdout.write(
                    f"ID: {payment.id} | User: {payment.user.email} | "
                    f"Amount: ${payment.amount} | "
                    f"Status: " + status_color(payment.status.upper()) +
                    f" | Date: {payment.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
        else:
            self.stdout.write(self.style.WARNING("No payment records found"))
        
        # Stripe data
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("  🔗 Stripe Integration Status"))
        self.stdout.write("="*60 + "\n")
        
        subs_with_stripe = UserSubscription.objects.exclude(stripe_subscription_id__isnull=True).exclude(stripe_subscription_id='').count()
        payments_with_stripe = PaymentHistory.objects.exclude(stripe_payment_intent_id__isnull=True).exclude(stripe_payment_intent_id='').count()
        
        self.stdout.write(f"Subscriptions with Stripe ID: {subs_with_stripe}/{subscription_count}")
        self.stdout.write(f"Payments with Stripe ID: {payments_with_stripe}/{payment_count}")
        
        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("  ✅ Summary"))
        self.stdout.write("="*60 + "\n")
        
        if subscription_count > 0 and payment_count > 0:
            self.stdout.write(self.style.SUCCESS("✅ Webhook is working! Records are being created."))
        elif subscription_count == 0 and payment_count == 0:
            self.stdout.write(self.style.WARNING("⚠️  No records found. Webhook may not be receiving events."))
            self.stdout.write("\nTroubleshooting:")
            self.stdout.write("1. Ensure Stripe CLI is running: stripe listen --forward-to localhost:8000/api/subscriptions/webhook/")
            self.stdout.write("2. Check webhook signing secret in settings.py")
            self.stdout.write("3. Make a test payment and check Django logs")
            self.stdout.write("4. Run: python manage.py test_webhook")
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Found {subscription_count} subscriptions and {payment_count} payments"))
        
        self.stdout.write("")
