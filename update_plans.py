"""
Script to verify and update subscription plans
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from subscriptions.models import SubscriptionPlan

# Check existing plans
plans = SubscriptionPlan.objects.all()
print(f"Found {plans.count()} plans:")
for plan in plans:
    print(f"\n{plan.name} - ${plan.price}/{plan.billing_cycle}")
    print(f"  Max requests: {plan.max_requests_per_month}")
    print(f"  Basic identity: {plan.basic_identity_verification}")
    print(f"  Criminal records: {plan.criminal_records_search}")
    print(f"  Federal records: {plan.federal_records_search}")
    print(f"  Employment verification: {plan.employment_verification}")
    print(f"  Education verification: {plan.education_verification}")
    print(f"  Priority support: {plan.priority_support}")
    print(f"  Advanced reports: {plan.advanced_reports}")
    print(f"  Stripe Price ID: {plan.stripe_price_id}")

# Update Basic Plan ($25)
print("\n\n=== Updating Basic Plan ===")
basic_plan = SubscriptionPlan.objects.filter(price=25).first()
if basic_plan:
    basic_plan.name = "Basic Plan"
    basic_plan.description = "Perfect for individuals needing basic background checks"
    basic_plan.max_requests_per_month = 5
    basic_plan.basic_identity_verification = True
    basic_plan.criminal_records_search = True
    basic_plan.federal_records_search = False
    basic_plan.employment_verification = False
    basic_plan.education_verification = False
    basic_plan.priority_support = False
    basic_plan.advanced_reports = False
    basic_plan.api_access = True
    basic_plan.save()
    print(f"✅ Updated: {basic_plan.name}")
else:
    print("❌ Basic Plan ($25) not found!")

# Update Premium Plan ($50)
print("\n=== Updating Premium Plan ===")
premium_plan = SubscriptionPlan.objects.filter(price=50).first()
if premium_plan:
    premium_plan.name = "Premium Plan"
    premium_plan.description = "Complete verification solution with unlimited requests"
    premium_plan.max_requests_per_month = 999999  # Unlimited
    premium_plan.basic_identity_verification = True
    premium_plan.criminal_records_search = True
    premium_plan.federal_records_search = True
    premium_plan.employment_verification = True
    premium_plan.education_verification = True
    premium_plan.priority_support = True
    premium_plan.advanced_reports = True
    premium_plan.api_access = True
    premium_plan.save()
    print(f"✅ Updated: {premium_plan.name}")
else:
    print("❌ Premium Plan ($50) not found!")

print("\n\n=== Final Plans ===")
for plan in SubscriptionPlan.objects.all().order_by('price'):
    print(f"\n{plan.name} - ${plan.price}/{plan.billing_cycle}")
    features = []
    if plan.basic_identity_verification:
        features.append("✓ Basic identity verification")
    if plan.criminal_records_search:
        features.append("✓ County criminal records search")
    if plan.federal_records_search:
        features.append("✓ Federal, state & county criminal records")
    if plan.employment_verification:
        features.append("✓ Employment history verification")
    if plan.education_verification:
        features.append("✓ Education verification")
    if plan.api_access:
        features.append("✓ API Access")
    if plan.priority_support:
        features.append("✓ Priority Support")
    else:
        features.append("✓ Standard support")
    if plan.advanced_reports:
        features.append("✓ 30-day report access")
    
    if plan.max_requests_per_month > 900000:
        features.append("✓ Unlimited requests")
    else:
        features.append(f"✓ Up to {plan.max_requests_per_month} requests per month")
    
    for f in features:
        print(f"  {f}")
