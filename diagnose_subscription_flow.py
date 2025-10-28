#!/usr/bin/env python
"""
Complete Subscription Flow Diagnostic & Fix Tool
Tests the entire flow: Register → Login → Subscribe → Submit Request
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from subscriptions.models import SubscriptionPlan, UserSubscription
from authentication.models import User
from background_requests.models import Request
from django.conf import settings

print("\n" + "="*70)
print("SUBSCRIPTION PROCESS DIAGNOSTIC TOOL")
print("="*70 + "\n")

# Issue 1: Check Stripe Configuration
print("1️⃣  STRIPE CONFIGURATION CHECK")
print("-" * 70)
issues = []

stripe_secret = getattr(settings, 'STRIPE_TEST_SECRET_KEY', None)
stripe_public = getattr(settings, 'STRIPE_TEST_PUBLIC_KEY', None)
stripe_webhook = getattr(settings, 'STRIPE_TEST_ENDPOINT_SECRET', None)

if not stripe_secret or stripe_secret == 'your-secret-key':
    issues.append("❌ STRIPE_TEST_SECRET_KEY not configured properly")
    print("   ❌ STRIPE_TEST_SECRET_KEY: Not set or using default")
else:
    print(f"   ✅ STRIPE_TEST_SECRET_KEY: Set (sk_test_...{stripe_secret[-10:]})")

if not stripe_public or stripe_public == 'your-public-key':
    issues.append("❌ STRIPE_TEST_PUBLIC_KEY not configured properly")
    print("   ❌ STRIPE_TEST_PUBLIC_KEY: Not set or using default")
else:
    print(f"   ✅ STRIPE_TEST_PUBLIC_KEY: Set (pk_test_...{stripe_public[-10:]})")

if not stripe_webhook:
    issues.append("⚠️  STRIPE_TEST_ENDPOINT_SECRET not set (webhook won't work)")
    print("   ⚠️  STRIPE_TEST_ENDPOINT_SECRET: Not set")
else:
    print(f"   ✅ STRIPE_TEST_ENDPOINT_SECRET: Set")

# Issue 2: Check Active Plans with Stripe Price IDs
print("\n2️⃣  ACTIVE SUBSCRIPTION PLANS CHECK")
print("-" * 70)

active_plans = SubscriptionPlan.objects.filter(is_active=True)
print(f"   Total Active Plans: {active_plans.count()}")

if active_plans.count() == 0:
    issues.append("❌ No active subscription plans available")
    print("   ❌ ERROR: No active plans found!")
else:
    plans_ok = 0
    for plan in active_plans:
        if not plan.stripe_price_id or plan.stripe_price_id == 'NOT SET':
            issues.append(f"❌ Plan '{plan.name}' is active but missing Stripe Price ID")
            print(f"   ❌ {plan.name}: Missing Stripe Price ID")
        else:
            plans_ok += 1
            print(f"   ✅ {plan.name}: ${plan.price}/{plan.billing_cycle} (Price ID: {plan.stripe_price_id})")
    
    if plans_ok == 0:
        issues.append("❌ All active plans are missing Stripe Price IDs")

# Issue 3: Check User Staff Status
print("\n3️⃣  USER REGISTRATION CHECK")
print("-" * 70)

total_users = User.objects.count()
staff_users = User.objects.filter(is_staff=True).count()
non_staff_users = User.objects.filter(is_staff=False, is_superuser=False).count()

print(f"   Total Users: {total_users}")
print(f"   Staff Users: {staff_users}")
print(f"   Non-Staff Users: {non_staff_users}")

if non_staff_users > 0:
    issues.append(f"⚠️  {non_staff_users} users don't have staff status (can't subscribe)")
    print(f"   ⚠️  WARNING: {non_staff_users} users without staff status")
    print("      These users cannot purchase subscriptions!")
else:
    print("   ✅ All users have staff status")

# Issue 4: Check Existing Subscriptions
print("\n4️⃣  EXISTING SUBSCRIPTIONS CHECK")
print("-" * 70)

subscriptions = UserSubscription.objects.all()
print(f"   Total Subscriptions: {subscriptions.count()}")

active_subs = subscriptions.filter(status='active')
print(f"   Active Subscriptions: {active_subs.count()}")

if subscriptions.exists():
    for sub in subscriptions[:5]:  # Show first 5
        print(f"   • {sub.user.username}: {sub.plan.name if sub.plan else 'No Plan'} ({sub.status})")

# Issue 5: Check Background Check Requests
print("\n5️⃣  BACKGROUND CHECK REQUESTS CHECK")
print("-" * 70)

total_requests = Request.objects.count()
print(f"   Total Requests: {total_requests}")

if total_requests > 0:
    pending = Request.objects.filter(status='Pending').count()
    in_progress = Request.objects.filter(status='In Progress').count()
    completed = Request.objects.filter(status='Completed').count()
    
    print(f"   • Pending: {pending}")
    print(f"   • In Progress: {in_progress}")
    print(f"   • Completed: {completed}")

# Summary of Issues
print("\n" + "="*70)
print("ISSUES FOUND")
print("="*70 + "\n")

if not issues:
    print("✅ NO ISSUES FOUND! Everything looks good.")
else:
    print(f"Found {len(issues)} issue(s):\n")
    for i, issue in enumerate(issues, 1):
        print(f"{i}. {issue}")

# Solutions
print("\n" + "="*70)
print("SOLUTIONS")
print("="*70 + "\n")

if "STRIPE_TEST_SECRET_KEY" in str(issues):
    print("🔧 FIX STRIPE CONFIGURATION:")
    print("   1. Go to Stripe Dashboard (https://dashboard.stripe.com/test/apikeys)")
    print("   2. Copy your test API keys")
    print("   3. Update your .env file:")
    print("      STRIPE_TEST_SECRET_KEY=sk_test_...")
    print("      STRIPE_TEST_PUBLIC_KEY=pk_test_...")
    print()

if "missing Stripe Price ID" in str(issues).lower():
    print("🔧 FIX MISSING STRIPE PRICE IDs:")
    print("   1. Go to Stripe Dashboard → Products")
    print("   2. Create products with recurring prices")
    print("   3. Copy the Price ID (starts with 'price_')")
    print("   4. Update your plans via Django admin or shell:")
    print()
    print("   Python Shell Commands:")
    for plan in active_plans:
        if not plan.stripe_price_id or plan.stripe_price_id == 'NOT SET':
            print(f"   >>> plan = SubscriptionPlan.objects.get(id={plan.id})")
            print(f"   >>> plan.stripe_price_id = 'price_YOUR_STRIPE_PRICE_ID'")
            print(f"   >>> plan.save()")
            print()

if non_staff_users > 0:
    print("🔧 FIX NON-STAFF USERS:")
    print("   Option 1: Update existing users (if needed):")
    print("   >>> User.objects.filter(is_staff=False).update(is_staff=True)")
    print()
    print("   Option 2: New users automatically get staff status (already fixed)")
    print()

if active_plans.count() == 0:
    print("🔧 CREATE SUBSCRIPTION PLANS:")
    print("   >>> from subscriptions.models import SubscriptionPlan")
    print("   >>> SubscriptionPlan.objects.create(")
    print("       name='Basic Plan',")
    print("       price=9.99,")
    print("       billing_cycle='monthly',")
    print("       max_requests_per_month=10,")
    print("       description='Basic background check plan',")
    print("       stripe_price_id='price_YOUR_STRIPE_PRICE_ID',")
    print("       is_active=True")
    print("   )")
    print()

print("\n" + "="*70)
print("TESTING THE FLOW")
print("="*70 + "\n")

print("📝 Manual Testing Steps:")
print()
print("1. Register a new user:")
print("   POST /api/auth/register/")
print("   { \"email\": \"test@example.com\", \"password\": \"Test123!\", ")
print("     \"confirm_password\": \"Test123!\" }")
print()

print("2. Login:")
print("   POST /api/auth/login/")
print("   { \"email\": \"test@example.com\", \"password\": \"Test123!\" }")
print("   → Save the access token")
print()

print("3. View available plans:")
print("   GET /api/subscriptions/plans/")
print()

print("4. Create checkout session:")
print("   POST /api/subscriptions/create-checkout-session/")
print("   Headers: Authorization: Bearer <token>")
print("   { \"plan_id\": 1 }")
print()

print("5. Complete payment on Stripe Checkout")
print("   → Should redirect to success page")
print()

print("6. Submit a background check request:")
print("   POST /api/requests/api/")
print("   Headers: Authorization: Bearer <token>")
print("   { \"name\": \"John Doe\", \"email\": \"john@example.com\", ")
print("     \"phone_number\": \"+1234567890\", \"dob\": \"1990-01-01\", ")
print("     \"city\": \"New York\", \"state\": \"NY\" }")
print()

print("7. View your dashboard:")
print("   GET /api/requests/api/my-dashboard/")
print("   Headers: Authorization: Bearer <token>")
print()

print("\n🌐 Swagger UI (Easiest Way):")
print("   Open: http://127.0.0.1:8000/swagger/")
print("   Test all endpoints interactively!")
print()

print("="*70 + "\n")
