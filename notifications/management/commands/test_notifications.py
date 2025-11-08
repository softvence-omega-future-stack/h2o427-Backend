from django.core.management.base import BaseCommand
from django.utils import timezone
from authentication.models import User
from notifications.models import Notification, FCMDevice
from notifications.firebase_service import send_push_notification, initialize_firebase


class Command(BaseCommand):
    help = 'Test notification system - creates test notification and attempts to send push'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email of the user to send test notification to',
        )
        parser.add_argument(
            '--fcm-token',
            type=str,
            help='FCM device token to test push notification',
        )

    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("📱 Testing Notification System"))
        self.stdout.write("=" * 70)

        # Get user
        email = options.get('email')
        if email:
            try:
                user = User.objects.get(email=email)
                self.stdout.write(f"\n Found user: {user.username} ({user.email})")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"\n User with email '{email}' not found"))
                return
        else:
            user = User.objects.filter(is_active=True).first()
            if not user:
                self.stdout.write(self.style.ERROR("\n No active users found"))
                return
            self.stdout.write(f"\n Using first active user: {user.username} ({user.email})")

        # Test 1: Create notification in database
        self.stdout.write("\n" + "-" * 70)
        self.stdout.write("TEST 1: Creating Database Notification")
        self.stdout.write("-" * 70)
        
        try:
            notification = Notification.objects.create(
                recipient=user,
                type='system',
                category='general',
                title=' Test Notification',
                message=f'This is a test notification created at {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}',
                push_sent=False
            )
            self.stdout.write(self.style.SUCCESS(f" Created notification ID: {notification.id}"))
            self.stdout.write(f"   Title: {notification.title}")
            self.stdout.write(f"   Message: {notification.message}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to create notification: {e}"))
            return

        # Test 2: Check FCM devices
        self.stdout.write("\n" + "-" * 70)
        self.stdout.write("TEST 2: Checking FCM Devices")
        self.stdout.write("-" * 70)
        
        fcm_devices = FCMDevice.objects.filter(user=user, active=True)
        self.stdout.write(f"Found {fcm_devices.count()} active FCM device(s) for user")
        
        for device in fcm_devices:
            self.stdout.write(f"  - Device type: {device.device_type}")
            self.stdout.write(f"    Token: {device.registration_token[:50]}...")
            self.stdout.write(f"    Created: {device.created_at}")

        # Test 3: Initialize Firebase
        self.stdout.write("\n" + "-" * 70)
        self.stdout.write("TEST 3: Firebase Initialization")
        self.stdout.write("-" * 70)
        
        try:
            initialize_firebase()
            self.stdout.write(self.style.SUCCESS(" Firebase Admin SDK initialized"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f" Firebase initialization failed: {e}"))

        # Test 4: Send push notification
        self.stdout.write("\n" + "-" * 70)
        self.stdout.write("TEST 4: Sending Push Notification")
        self.stdout.write("-" * 70)

        fcm_token = options.get('fcm_token')
        
        if fcm_token:
            self.stdout.write(f"Using provided FCM token: {fcm_token[:50]}...")
            tokens_to_test = [fcm_token]
        elif fcm_devices.exists():
            self.stdout.write("Using registered device tokens...")
            tokens_to_test = list(fcm_devices.values_list('registration_token', flat=True))
        else:
            self.stdout.write(self.style.WARNING("  No FCM tokens available to test"))
            tokens_to_test = []

        if tokens_to_test:
            try:
                result = send_push_notification(
                    device_tokens=tokens_to_test,
                    title=' Test Push Notification',
                    body='This is a test push notification from your Django backend!',
                    data={
                        'test': 'true',
                        'notification_id': str(notification.id),
                        'timestamp': str(timezone.now())
                    }
                )
                
                self.stdout.write(f"\nPush notification result:")
                self.stdout.write(f"  Success count: {result.get('success_count', 0)}")
                self.stdout.write(f"  Failure count: {result.get('failure_count', 0)}")
                
                if result.get('success_count', 0) > 0:
                    self.stdout.write(self.style.SUCCESS("Push notification sent successfully!"))
                    self.stdout.write("   Check your device for the notification.")
                    
                    # Update notification
                    notification.push_sent = True
                    notification.push_sent_at = timezone.now()
                    notification.save()
                else:
                    self.stdout.write(self.style.WARNING("  Push notification failed to send"))
                
                if result.get('failed_tokens'):
                    self.stdout.write("\nFailed tokens:")
                    for failed in result['failed_tokens']:
                        self.stdout.write(f"  - Token: {failed['token'][:50]}...")
                        self.stdout.write(f"    Error: {failed['error']}")
                        
                        # Update notification with error
                        notification.push_error = failed['error']
                        notification.save()
                
                if result.get('error'):
                    self.stdout.write(self.style.ERROR(f"\nError: {result['error']}"))
                    notification.push_error = result['error']
                    notification.save()
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f" Exception: {e}"))
                notification.push_error = str(e)
                notification.save()

        # Test 5: Summary
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("SUMMARY")
        self.stdout.write("=" * 70)
        
        self.stdout.write(f"\n Database notification created (ID: {notification.id})")
        self.stdout.write(f"   Push sent: {notification.push_sent}")
        if notification.push_error:
            self.stdout.write(f"   Push error: {notification.push_error[:100]}")
        
        total_notifications = Notification.objects.filter(recipient=user).count()
        unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
        
        self.stdout.write(f"\nUser Statistics:")
        self.stdout.write(f"   Total notifications: {total_notifications}")
        self.stdout.write(f"   Unread: {unread_count}")
        self.stdout.write(f"   Active devices: {fcm_devices.count()}")
        
        # Instructions
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("NEXT STEPS")
        self.stdout.write("=" * 70)
        
        if not fcm_devices.exists() and not fcm_token:
            self.stdout.write("\n To test push notifications:")
            self.stdout.write("   1. Register an FCM device via API:")
            self.stdout.write("      POST /api/notifications/fcm-devices/")
            self.stdout.write("   2. Or run this command with --fcm-token option")
        
        if 'The requested URL /batch was not found' in str(notification.push_error):
            self.stdout.write("\n  FCM API not enabled:")
            self.stdout.write("   1. Go to Google Cloud Console")
            self.stdout.write("   2. Enable 'Firebase Cloud Messaging API'")
            self.stdout.write("   3. Wait 5-10 minutes")
            self.stdout.write("   4. Run this command again")
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS(" Test Complete!"))
        self.stdout.write("=" * 70 + "\n")
