"""
Signals for background check requests
Automatically sends notifications when requests are created or updated
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Request, Report

User = get_user_model()


@receiver(post_save, sender=Request)
def send_request_notifications(sender, instance, created, **kwargs):
    """
    Send notifications when a background check request is created or updated
    
    - When created: Notify user (success) and admins (new request)
    - When status changes: Notify user about status update
    """
    from notifications.models import Notification
    from notifications.firebase_service import send_notification_to_user, send_notification_to_admins
    
    if created:
        # 1. Send success notification to the user who submitted the request
        user_notification = Notification.objects.create(
            recipient=instance.user,
            sender=None,  # System notification
            type=Notification.SYSTEM,
            category=Notification.BACKGROUND_CHECK,
            title='Background Check Request Submitted',
            message=f'Your background check request for {instance.name} has been successfully submitted. We will notify you once the verification is complete.',
            related_object_type='Request',
            related_object_id=instance.id
        )
        
        # Send push notification to user
        try:
            send_notification_to_user(
                user=instance.user,
                title='Request Submitted Successfully',
                body=f'Your background check request for {instance.name} has been received and is being processed.',
                notification_type='request_update',
                data={
                    'notification_id': str(user_notification.id),
                    'request_id': str(instance.id),
                    'type': 'request_created'
                }
            )
        except Exception as e:
            print(f"Failed to send push notification to user: {e}")
        
        # 2. Send notification to all admins about new request
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        
        for admin in admin_users:
            admin_notification = Notification.objects.create(
                recipient=admin,
                sender=instance.user,
                type=Notification.USER_TO_ADMIN,
                category=Notification.BACKGROUND_CHECK,
                title='New Background Check Request',
                message=f'New background check request received from {instance.user.username} for {instance.name}. Status: {instance.status}',
                related_object_type='Request',
                related_object_id=instance.id
            )
        
        # Send push notification to admins
        try:
            send_notification_to_admins(
                title='New Request Received',
                body=f'New background check request from {instance.user.username} for {instance.name}',
                notification_type='admin',
                data={
                    'request_id': str(instance.id),
                    'user_id': str(instance.user.id),
                    'type': 'new_request'
                }
            )
        except Exception as e:
            print(f"Failed to send push notification to admins: {e}")
    
    else:
        # Request was updated (not created)
        # Check if status has changed by comparing with database
        try:
            old_instance = Request.objects.get(pk=instance.pk)
            
            # Only send notification if status actually changed
            if hasattr(old_instance, 'status') and old_instance.status != instance.status:
                # Send status update notification to user
                status_notification = Notification.objects.create(
                    recipient=instance.user,
                    sender=None,
                    type=Notification.ADMIN_TO_USER,
                    category=Notification.BACKGROUND_CHECK,
                    title='Request Status Updated',
                    message=f'Your background check request for {instance.name} status has been updated to: {instance.status}',
                    related_object_type='Request',
                    related_object_id=instance.id
                )
                
                # Send push notification
                try:
                    send_notification_to_user(
                        user=instance.user,
                        title='Status Update',
                        body=f'Your request status: {instance.status}',
                        notification_type='request_update',
                        data={
                            'notification_id': str(status_notification.id),
                            'request_id': str(instance.id),
                            'status': instance.status,
                            'type': 'status_update'
                        }
                    )
                except Exception as e:
                    print(f"Failed to send status update push: {e}")
        
        except Request.DoesNotExist:
            # This shouldn't happen, but handle it gracefully
            pass


@receiver(post_save, sender=Report)
def send_report_ready_notification(sender, instance, created, **kwargs):
    """
    Send notification when a background check report is ready
    """
    from notifications.models import Notification
    from notifications.firebase_service import send_notification_to_user
    
    if created:
        # Send notification to user that their report is ready
        report_notification = Notification.objects.create(
            recipient=instance.request.user,
            sender=None,
            type=Notification.ADMIN_TO_USER,
            category=Notification.REPORT,
            title='Background Check Report Ready',
            message=f'Your background check report for {instance.request.name} is now ready for download.',
            related_object_type='Report',
            related_object_id=instance.id,
            action_url=f'/api/requests/{instance.request.id}/download-report/'
        )
        
        # Send push notification
        try:
            send_notification_to_user(
                user=instance.request.user,
                title='Report Ready',
                body=f'Your background check report for {instance.request.name} is ready!',
                notification_type='report_ready',
                data={
                    'notification_id': str(report_notification.id),
                    'request_id': str(instance.request.id),
                    'report_id': str(instance.id),
                    'type': 'report_ready'
                }
            )
        except Exception as e:
            print(f"Failed to send report ready push: {e}")
