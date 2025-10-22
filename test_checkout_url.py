"""
Quick Test Script for Stripe Checkout Payment URL
Run this to test the new payment URL endpoints
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("🚀 Testing Stripe Checkout Payment URL")
print("=" * 60)

# Step 1: Register a test user
print("\n1️⃣ Registering test user...")
register_data = {
    "username": "checkout_test_user",
    "email": "checkout_test@example.com",
    "password": "Test123!",
    "confirm_password": "Test123!"
}

try:
    response = requests.post(f"{BASE_URL}/api/auth/register/", json=register_data)
    if response.status_code == 201 or response.status_code == 200:
        print("✅ User registered successfully")
    else:
        print(f"⚠️  User may already exist: {response.status_code}")
except Exception as e:
    print(f"⚠️  Registration: {str(e)}")

# Step 2: Login
print("\n2️⃣ Logging in...")
login_data = {
    "email": "checkout_test@example.com",
    "password": "Test123!"
}

try:
    response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data)
    if response.status_code == 200:
        jwt_token = response.json().get('access')
        print("✅ Login successful")
        print(f"   JWT Token: {jwt_token[:50]}...")
        
        headers = {"Authorization": f"Bearer {jwt_token}"}
        
        # Step 3: Get available plans
        print("\n3️⃣ Fetching available plans...")
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans/")
        plans = response.json()
        print(f"✅ Found {len(plans)} plans:")
        for plan in plans:
            print(f"   • {plan['name']} - ${plan['price']}/{plan['billing_cycle']}")
        
        # Step 4: Create Checkout Session
        print("\n4️⃣ Creating Stripe Checkout Session...")
        checkout_data = {
            "plan_id": 1,  # Basic Plan
            "trial_period_days": 0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/subscriptions/checkout/create/",
            headers=headers,
            json=checkout_data
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Checkout session created successfully!")
            print(f"\n{'=' * 60}")
            print("📋 CHECKOUT SESSION DETAILS:")
            print(f"{'=' * 60}")
            print(f"Session ID: {data['session_id']}")
            print(f"\n🔗 PAYMENT URL:")
            print(f"{data['checkout_url']}")
            print(f"\n{'=' * 60}")
            print(f"\n💡 Next Steps:")
            print(f"1. Copy the payment URL above")
            print(f"2. Open it in your browser")
            print(f"3. Use test card: 4242 4242 4242 4242")
            print(f"4. Exp: 12/34  |  CVC: 123  |  ZIP: 12345")
            print(f"5. Complete the payment")
            print(f"6. You'll be redirected back to success page")
            print(f"\n{'=' * 60}")
            
            print(f"\n📊 Plan Details:")
            plan = data['plan']
            print(f"   Name: {plan['name']}")
            print(f"   Price: ${plan['price']}/{plan['billing_cycle']}")
            print(f"   Features:")
            for feature in plan['feature_list']:
                print(f"      ✓ {feature}")
            
        else:
            error_data = response.json()
            print(f"❌ Failed to create checkout session")
            print(f"   Error: {error_data.get('error', 'Unknown error')}")
            
    else:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 60)
print("✅ Test Complete!")
print("=" * 60)
print("\n📖 For more information, see:")
print("   • STRIPE_CHECKOUT_PAYMENT_URL.md")
print("   • HOW_TO_PURCHASE_SUBSCRIPTION.md")
print("=" * 60)
