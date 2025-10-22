"""
Script to keep only 2 plans active: Basic ($25) and Premium ($50)
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from subscriptions.models import SubscriptionPlan

# Get all plans
all_plans = SubscriptionPlan.objects.all()
print(f"Found {all_plans.count()} total plans\n")

# Deactivate all plans first
SubscriptionPlan.objects.all().update(is_active=False)
print("Deactivated all plans\n")

# Activate only Basic ($25) and Premium ($50)
basic_plan = SubscriptionPlan.objects.filter(price=25, name="Basic Plan").first()
if basic_plan:
    basic_plan.is_active = True
    basic_plan.save()
    print(f"✅ Activated: {basic_plan.name} - ${basic_plan.price}/{basic_plan.billing_cycle}")
else:
    print("❌ Basic Plan ($25) not found!")

premium_plan = SubscriptionPlan.objects.filter(price=50, name="Premium Plan").first()
if premium_plan:
    premium_plan.is_active = True
    premium_plan.save()
    print(f"✅ Activated: {premium_plan.name} - ${premium_plan.price}/{premium_plan.billing_cycle}")
else:
    print("❌ Premium Plan ($50) not found!")

print("\n=== Active Plans (will show in UI) ===")
active_plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
for plan in active_plans:
    print(f"\n{plan.name} - ${plan.price}/{plan.billing_cycle}")
    print(f"  Stripe Price ID: {plan.stripe_price_id}")
    print(f"  Max Requests: {plan.max_requests_per_month}")

print("\n=== Inactive Plans (hidden) ===")
inactive_plans = SubscriptionPlan.objects.filter(is_active=False)
for plan in inactive_plans:
    print(f"  ❌ {plan.name} - ${plan.price}")

print(f"\n✅ Done! Only {active_plans.count()} plans are now active.")
