"""
Test Forgot Password Endpoint
"""

import os
import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

def test_forgot_password():
    """Test the forgot password endpoint"""
    print("=" * 60)
    print("🔐 TESTING FORGOT PASSWORD ENDPOINT")
    print("=" * 60)
    
    # Create API client
    client = APIClient()
    
    # Check if test user exists, create if not
    test_email = "anower.softvence@gmail.com"
    
    print(f"\n1️⃣ Checking if user '{test_email}' exists...")
    user, created = User.objects.get_or_create(
        email=test_email,
        defaults={
            'username': 'testuser',
        }
    )
    
    if created:
        user.set_password('Test123!')
        user.save()
        print(f"   ✅ User created: {user.username}")
    else:
        print(f"   ✅ User found: {user.username}")
    
    print(f"\n2️⃣ Sending forgot password request...")
    
    # Make request
    response = client.post('/api/auth/forgot-password/', {
        'email': test_email
    }, format='json')
    
    print(f"   Status Code: {response.status_code}")
    print(f"   Response: {response.data}")
    
    if response.status_code == 200:
        print("\n   ✅ SUCCESS! Password reset email sent!")
        print(f"   📨 Check your inbox: {test_email}")
        print("\n   The email contains a reset link like:")
        print("   http://localhost:3000/reset-password?token=...")
    else:
        print(f"\n   ❌ FAILED! Status: {response.status_code}")
        print(f"   Error: {response.data}")

if __name__ == "__main__":
    test_forgot_password()
