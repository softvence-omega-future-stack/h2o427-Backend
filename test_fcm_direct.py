import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from notifications.firebase_service import initialize_firebase, send_push_notification

def test_direct_notification():
    """Send a test notification directly to FCM token"""
    
    # Your FCM token
    fcm_token = "cvF30bCQQOWhd3ZDzdikrl:APA91bFTeDckJySEQ989h7r2Fb8WCFl8j2LejX8MEUjYuVJv0xsX-UIhhmjCCV0q3yaxL9ZaWJ7YiePLVGOHZW1QageWJaZnVIx0-MvPS2q_2xzWMyaCbsI"
    
    print("=" * 60)
    print("Testing Direct FCM Push Notification")
    print("=" * 60)
    
    # Initialize Firebase
    print("\n1. Initializing Firebase Admin SDK...")
    try:
        initialize_firebase()
        print("   Firebase initialized successfully")
    except Exception as e:
        print(f"   Failed to initialize Firebase: {e}")
        return
    
    # Send test notification
    print("\n2. Sending test notification...")
    print(f"   Token: {fcm_token[:50]}...")
    
    title = "Test Notification from Django"
    body = "This is a test push notification sent directly from your backend!"
    
    data = {
        "test": "true",
        "source": "django_backend",
        "notification_type": "test"
    }
    
    try:
        result = send_push_notification(
            device_tokens=fcm_token,
            title=title,
            body=body,
            data=data
        )
        
        print("\n3. Results:")
        print(f"   Success count: {result.get('success_count', 0)}")
        print(f"   Failure count: {result.get('failure_count', 0)}")
        
        if result.get('failed_tokens'):
            print("\n   Failed tokens:")
            for failed in result['failed_tokens']:
                print(f"  Token: {failed['token'][:50]}...")
                print(f"  Error: {failed['error']}")
        
        if result.get('error'):
            print(f"\n   Error: {result['error']}")

        if result.get('success_count', 0) > 0:
            print("\n   Notification sent successfully!")
            print("   Check your device for the notification.")
        else:
            print("\n   Failed to send notification.")
            
    except Exception as e:
        print(f"\n   Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_direct_notification()
