"""
Generate a valid password reset link for testing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from authentication.models import User

# Get first user
user = User.objects.first()

if user:
    # Generate token
    uid = urlsafe_base64_encode(str(user.pk).encode())
    token = default_token_generator.make_token(user)
    
    # Generate URLs
    local_url = f"http://127.0.0.1:8000/reset-password/{uid}/{token}/"
    production_url = f"https://h2o427-backend-u9bx.onrender.com/reset-password/{uid}/{token}/"
    
    print("=" * 70)
    print("✅ PASSWORD RESET LINK GENERATED")
    print("=" * 70)
    print(f"User: {user.username} (ID: {user.id})")
    print(f"Email: {user.email}")
    print()
    print("LOCAL TESTING:")
    print(local_url)
    print()
    print("PRODUCTION:")
    print(production_url)
    print("=" * 70)
    print()
    print("🌐 Click the LOCAL link to test the password reset page!")
    print()
else:
    print("❌ No users found in database")
