"""
Test script for Twilio SMS OTP functionality
Run this to verify your Twilio configuration is working
"""

import os
import sys
import django
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from django.conf import settings

def check_twilio_config():
    """Check if Twilio is properly configured"""
    print("=" * 60)
    print("🔍 TWILIO CONFIGURATION CHECK")
    print("=" * 60)
    
    # Check environment variables
    checks = {
        'TWILIO_ACCOUNT_SID': getattr(settings, 'TWILIO_ACCOUNT_SID', None),
        'TWILIO_AUTH_TOKEN': getattr(settings, 'TWILIO_AUTH_TOKEN', None),
        'TWILIO_FROM_NUMBER': getattr(settings, 'TWILIO_FROM_NUMBER', None),
    }
    
    all_configured = True
    
    for key, value in checks.items():
        if value:
            masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            print(f"✅ {key}: {masked_value}")
        else:
            print(f"❌ {key}: NOT SET")
            all_configured = False
    
    print(f"\n📞 OTP TTL: {getattr(settings, 'PHONE_OTP_TTL_SECONDS', 300)} seconds")
    
    if not all_configured:
        print("\n⚠️  WARNING: Twilio is not fully configured!")
        print("Please set the missing environment variables in your .env file")
        return False
    
    return True


def test_twilio_connection():
    """Test actual connection to Twilio API"""
    print("\n" + "=" * 60)
    print("🧪 TESTING TWILIO CONNECTION")
    print("=" * 60)
    
    try:
        from twilio.rest import Client
        
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        # Fetch account info to verify credentials
        account = client.api.accounts(settings.TWILIO_ACCOUNT_SID).fetch()
        
        print(f"✅ Connected to Twilio successfully!")
        print(f"📱 Account Status: {account.status}")
        print(f"👤 Account Name: {account.friendly_name}")
        
        # Check balance (trial accounts show this differently)
        try:
            balance = client.api.accounts(settings.TWILIO_ACCOUNT_SID).balance.fetch()
            print(f"💰 Account Balance: {balance.balance} {balance.currency}")
        except:
            print(f"💰 Account Balance: Trial account (check console for credits)")
        
        return True
        
    except ImportError:
        print("❌ Twilio library not installed!")
        print("Run: pip install twilio")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        print("\nPossible issues:")
        print("  1. Invalid Account SID or Auth Token")
        print("  2. Network connection problem")
        print("  3. Check your credentials in .env file")
        return False


def send_test_sms():
    """Send a test SMS (optional)"""
    print("\n" + "=" * 60)
    print("📤 SEND TEST SMS")
    print("=" * 60)
    
    phone = input("\n📞 Enter a VERIFIED phone number (or press Enter to skip): ").strip()
    
    if not phone:
        print("⏭️  Skipping test SMS")
        return
    
    if not phone.startswith('+'):
        print("⚠️  Phone number should start with + (e.g., +1234567890)")
        return
    
    try:
        from twilio.rest import Client
        
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        print(f"\n📨 Sending test SMS to {phone}...")
        
        message = client.messages.create(
            body="Test message from your Django app! Twilio is working! 🎉",
            from_=settings.TWILIO_FROM_NUMBER,
            to=phone
        )
        
        print(f"✅ SMS sent successfully!")
        print(f"📋 Message SID: {message.sid}")
        print(f"📊 Status: {message.status}")
        print(f"\n💡 Check your phone for the message!")
        print(f"📱 Monitor logs at: https://console.twilio.com/us1/monitor/logs/sms")
        
    except Exception as e:
        print(f"❌ Failed to send SMS: {str(e)}")
        print("\n⚠️  Common issues:")
        print("  1. Phone number not verified (trial account)")
        print("  2. Invalid phone number format")
        print("  3. Insufficient credits")
        print(f"\n📋 Verify your number at:")
        print(f"   https://console.twilio.com/us1/develop/phone-numbers/manage/verified")


def main():
    print("\n" + "🔔" * 30)
    print("   TWILIO SMS OTP TEST UTILITY")
    print("🔔" * 30 + "\n")
    
    # Step 1: Check configuration
    if not check_twilio_config():
        print("\n❌ Configuration check failed. Fix the issues above and try again.")
        return
    
    # Step 2: Test connection
    if not test_twilio_connection():
        print("\n❌ Connection test failed. Check your credentials.")
        return
    
    # Step 3: Optional test SMS
    send_test_sms()
    
    print("\n" + "=" * 60)
    print("✅ TWILIO SETUP CHECK COMPLETE!")
    print("=" * 60)
    print("\n📚 Next steps:")
    print("  1. Register a user with a phone number")
    print("  2. Check your phone for the OTP code")
    print("  3. Verify the OTP using /api/auth/verify-otp/")
    print(f"\n🚀 Your app is ready to send SMS! 🎉\n")


if __name__ == '__main__':
    main()
