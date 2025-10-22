"""
Complete Password Reset Flow Test
Tests the entire forgot password → reset password flow
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
import re

User = get_user_model()

def extract_reset_token_from_url(url):
    """Extract uid and token from reset URL"""
    # Pattern: /reset-password/uid/token/
    pattern = r'/reset-password/([^/]+)/([^/]+)/'
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def test_complete_flow():
    """Test the complete password reset flow"""
    print("=" * 70)
    print("🔐 COMPLETE PASSWORD RESET FLOW TEST")
    print("=" * 70)
    
    client = APIClient()
    test_email = "anower.softvence@gmail.com"
    
    # Step 1: Request password reset
    print("\n📧 STEP 1: Request Password Reset")
    print("-" * 70)
    response = client.post('/api/auth/forgot-password/', {
        'email': test_email
    }, format='json')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.data}")
    
    if response.status_code != 200:
        print("❌ Failed to send reset email!")
        return
    
    print("✅ Reset email sent successfully!")
    print("\n⚠️  CHECK YOUR EMAIL for the reset link!")
    print("The email will contain a URL like:")
    print("http://127.0.0.1:8000/api/auth/reset-password/Mg/c6qovq-abc123...def456/")
    
    # Manual input for testing
    print("\n" + "=" * 70)
    print("📝 STEP 2: Extract Token from Email")
    print("-" * 70)
    print("Copy the reset URL from your email and paste it here")
    print("Example: http://127.0.0.1:8000/api/auth/reset-password/Mg/c6qovq-abc/")
    
    reset_url = input("\nPaste the reset URL here: ").strip()
    
    if not reset_url:
        print("\n⚠️  No URL provided. Using example for demonstration...")
        print("\nTo test manually:")
        print("1. Check email for reset link")
        print("2. Extract uid and token from URL")
        print("3. Use Postman to test (see guide below)")
        return
    
    # Extract uid and token
    uid, token = extract_reset_token_from_url(reset_url)
    
    if not uid or not token:
        print("❌ Could not extract uid and token from URL")
        print("URL format should be: /reset-password/UID/TOKEN/")
        return
    
    print(f"\n✅ Extracted tokens:")
    print(f"   UID: {uid}")
    print(f"   Token: {token[:20]}...")
    
    # Step 3: Validate token
    print("\n" + "=" * 70)
    print("🔍 STEP 3: Validate Reset Token")
    print("-" * 70)
    
    response = client.get(f'/api/auth/reset-password/{uid}/{token}/')
    print(f"Status: {response.status_code}")
    print(f"Response: {response.data}")
    
    if response.status_code != 200:
        print("❌ Token validation failed!")
        return
    
    print("✅ Token is valid!")
    
    # Step 4: Reset password
    print("\n" + "=" * 70)
    print("🔑 STEP 4: Reset Password")
    print("-" * 70)
    
    new_password = "NewPassword123!"
    
    response = client.post('/api/auth/reset-password/', {
        'uid': uid,
        'token': token,
        'new_password': new_password,
        'confirm_new_password': new_password
    }, format='json')
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.data}")
    
    if response.status_code != 200:
        print("❌ Password reset failed!")
        return
    
    print("✅ Password reset successfully!")
    
    # Step 5: Test login with new password
    print("\n" + "=" * 70)
    print("🔓 STEP 5: Test Login with New Password")
    print("-" * 70)
    
    response = client.post('/api/auth/login/', {
        'email': test_email,
        'password': new_password
    }, format='json')
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Login successful with new password!")
        print(f"Access Token: {response.data['access'][:50]}...")
    else:
        print(f"❌ Login failed: {response.data}")
    
    print("\n" + "=" * 70)
    print("✅ COMPLETE FLOW TEST FINISHED!")
    print("=" * 70)

if __name__ == "__main__":
    try:
        test_complete_flow()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
