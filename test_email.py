"""
Email Configuration Test Script
Tests if email settings are working correctly
"""

import os
import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email_settings():
    """Test email configuration"""
    print("=" * 60)
    print("📧 EMAIL CONFIGURATION TEST")
    print("=" * 60)
    
    print("\n1️⃣ Current Email Settings:")
    print(f"   Backend: {settings.EMAIL_BACKEND}")
    print(f"   Host: {settings.EMAIL_HOST}")
    print(f"   Port: {settings.EMAIL_PORT}")
    print(f"   Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"   Username: {settings.EMAIL_HOST_USER}")
    print(f"   Password: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"   From Email: {settings.DEFAULT_FROM_EMAIL}")
    
    print("\n2️⃣ Testing Email Connection...")
    
    try:
        # Try to send a test email
        result = send_mail(
            subject='Test Email from Background Check System',
            message='This is a test email to verify email configuration.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.EMAIL_HOST_USER],  # Send to yourself
            fail_silently=False,
        )
        
        if result == 1:
            print("   ✅ SUCCESS! Email sent successfully!")
            print(f"   📨 Check your inbox: {settings.EMAIL_HOST_USER}")
        else:
            print("   ❌ FAILED! Email was not sent.")
            
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
        print("\n3️⃣ Troubleshooting Suggestions:")
        
        if "getaddrinfo failed" in str(e):
            print("   🔍 Network/DNS Issue Detected!")
            print("   Solutions:")
            print("   1. Check your internet connection")
            print("   2. Try using a different DNS (8.8.8.8)")
            print("   3. Disable VPN/Proxy if active")
            print("   4. Check firewall settings")
            
        elif "Authentication failed" in str(e) or "Username and Password not accepted" in str(e):
            print("   🔐 Authentication Issue Detected!")
            print("   Solutions:")
            print("   1. Enable 'Less secure app access' in Gmail")
            print("   2. Use Gmail App Password instead:")
            print("      a. Go to: https://myaccount.google.com/apppasswords")
            print("      b. Generate new app password")
            print("      c. Update EMAIL_HOST_PASSWORD in .env")
            print("   3. Enable 2-Step Verification first")
            
        elif "Connection refused" in str(e):
            print("   🚫 Connection Refused!")
            print("   Solutions:")
            print("   1. Check if port 587 is blocked")
            print("   2. Try port 465 with EMAIL_USE_SSL=True")
            print("   3. Check firewall/antivirus settings")
            
        else:
            print(f"   Unknown error. Full details: {e}")

if __name__ == "__main__":
    test_email_settings()
