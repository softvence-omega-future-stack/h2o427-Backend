"""
Test script for the Notification System
Run with: python manage.py shell < test_notifications.py
Or: python test_notifications.py
"""

import os
import sys
import django

# Setup Django environment
if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
    django.setup()

from django.contrib.auth import get_user_model
from notifications.models import Notification
from notifications.signals import send_user_notification, send_admin_notification

User = get_user_model()


def test_notification_system():
    """Test the notification system"""
    
    print("=" * 60)
    print("Testing Notification System")
    print("=" * 60)
    
    # 1. Create test users if they don't exist
    print("\n1. Setting up test users...")
    
    # Create regular user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'testuser@example.com',
            'full_name': 'Test User'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"   ✓ Created regular user: {user.username}")
    else:
        print(f"   ℹ Using existing user: {user.username}")
    
    # Create admin user
    admin, created = User.objects.get_or_create(
        username='testadmin',
        defaults={
            'email': 'testadmin@example.com',
            'full_name': 'Test Admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin.set_password('adminpass123')
        admin.save()
        print(f"   ✓ Created admin user: {admin.username}")
    else:
        admin.is_staff = True
        admin.is_superuser = True
        admin.save()
        print(f"   ℹ Using existing admin: {admin.username}")
    
    # 2. Test creating different types of notifications
    print("\n2. Creating test notifications...")
    
    # Admin to User notification
    notif1 = Notification.objects.create(
        recipient=user,
        sender=admin,
        type=Notification.ADMIN_TO_USER,
        category=Notification.GENERAL,
        title='Welcome Message',
        message='Welcome to our platform! We are glad to have you.'
    )
    print(f"   ✓ Created Admin → User notification (ID: {notif1.id})")
    
    # User to Admin notification
    notif2 = Notification.objects.create(
        recipient=admin,
        sender=user,
        type=Notification.USER_TO_ADMIN,
        category=Notification.GENERAL,
        title='Help Request',
        message='I need help with my account settings.'
    )
    print(f"   ✓ Created User → Admin notification (ID: {notif2.id})")
    
    # System notification
    notif3 = Notification.objects.create(
        recipient=user,
        sender=None,
        type=Notification.SYSTEM,
        category=Notification.BACKGROUND_CHECK,
        title='Background Check Status',
        message='Your background check request has been received.',
        related_object_type='Request',
        related_object_id=1
    )
    print(f"   ✓ Created System notification (ID: {notif3.id})")
    
    # 3. Test helper functions
    print("\n3. Testing helper functions...")
    
    notif4 = send_user_notification(
        recipient_user=user,
        title='Payment Confirmed',
        message='Your payment has been processed successfully.',
        category=Notification.PAYMENT,
        sender=admin
    )
    print(f"   ✓ Created notification using send_user_notification (ID: {notif4.id})")
    
    count = send_admin_notification(
        sender_user=user,
        title='New User Registration',
        message='A new user has registered.',
        category=Notification.GENERAL
    )
    print(f"   ✓ Created {count} notification(s) using send_admin_notification")
    
    # 4. Test notification queries
    print("\n4. Testing notification queries...")
    
    user_notifications = Notification.objects.filter(recipient=user)
    print(f"   ✓ User has {user_notifications.count()} notifications")
    
    admin_notifications = Notification.objects.filter(recipient=admin)
    print(f"   ✓ Admin has {admin_notifications.count()} notifications")
    
    unread_count = user_notifications.filter(is_read=False).count()
    print(f"   ✓ User has {unread_count} unread notifications")
    
    # 5. Test mark as read functionality
    print("\n5. Testing mark as read/unread...")
    
    if user_notifications.filter(is_read=False).exists():
        first_unread = user_notifications.filter(is_read=False).first()
        print(f"   ℹ Notification {first_unread.id} is unread")
        
        first_unread.mark_as_read()
        print(f"   ✓ Marked notification {first_unread.id} as read")
        
        first_unread.mark_as_unread()
        print(f"   ✓ Marked notification {first_unread.id} as unread")
    
    # 6. Display notification summary
    print("\n6. Notification Summary:")
    print("-" * 60)
    
    for notif in Notification.objects.all().order_by('-created_at')[:5]:
        status = "READ" if notif.is_read else "UNREAD"
        sender_name = notif.sender.username if notif.sender else "System"
        print(f"   [{status}] {notif.get_type_display()}")
        print(f"           From: {sender_name} → To: {notif.recipient.username}")
        print(f"           Title: {notif.title}")
        print(f"           Category: {notif.get_category_display()}")
        print(f"           Created: {notif.created_at}")
        print()
    
    # 7. Final statistics
    print("\n7. System Statistics:")
    print("-" * 60)
    print(f"   Total Notifications: {Notification.objects.count()}")
    print(f"   Admin → User: {Notification.objects.filter(type=Notification.ADMIN_TO_USER).count()}")
    print(f"   User → Admin: {Notification.objects.filter(type=Notification.USER_TO_ADMIN).count()}")
    print(f"   System: {Notification.objects.filter(type=Notification.SYSTEM).count()}")
    print(f"   Unread: {Notification.objects.filter(is_read=False).count()}")
    print(f"   Read: {Notification.objects.filter(is_read=True).count()}")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run migrations: python manage.py makemigrations notifications")
    print("2. Apply migrations: python manage.py migrate")
    print("3. Access admin panel: /admin/notifications/notification/")
    print("4. Test API: /api/notifications/")
    print("=" * 60)


if __name__ == '__main__':
    test_notification_system()
