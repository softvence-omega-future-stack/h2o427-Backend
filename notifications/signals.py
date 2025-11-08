from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.apps import apps
from django.utils import timezone
from .models import Notification
from .firebase_service import send_notification_to_user, send_notification_to_admins
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender='background_requests.Request')
def notify_on_request_status_change(sender, instance, created, **kwargs):
    """
    Send notification when background check request status changes
    """
    if created:
        # Notify all admins when a new request is submitted
        admin_users = User.objects.filter(is_staff=True)
        
        notifications = []
        for admin in admin_users:
            notification = Notification.objects.create(
                recipient=admin,
                sender=instance.user,
                type=Notification.USER_TO_ADMIN,
                category=Notification.BACKGROUND_CHECK,
                title='New Background Check Request',
                message=f'{instance.user.username} has submitted a new background check request for {instance.name}.',
                related_object_type='Request',
                related_object_id=instance.id,
                action_url=f'/admin/background_requests/request/{instance.id}/change/',
                push_sent=False
            )
            notifications.append(notification)
        
        # Send push notification to admins
        try:
            title = 'New Background Check Request'
            message = f'{instance.user.username} has submitted a new background check request.'
            result = send_notification_to_admins(
                title,
                message,
                notification_type='background_check',
                data={
                    'request_id': str(instance.id),
                    'type': 'new_request'
                }
            )
            
            # Update push status for all admin notifications
            if result.get('success_count', 0) > 0:
                for notification in notifications:
                    notification.push_sent = True
                    notification.push_sent_at = timezone.now()
                    notification.save()
                
            logger.info(f"Sent push notifications to {result.get('success_count', 0)} admin devices")
        except Exception as e:
            logger.error(f"Failed to send push notification to admins: {str(e)}")
        
        # Notify user that their request was received
        user_notification = Notification.objects.create(
            recipient=instance.user,
            sender=None,  # System notification
            type=Notification.SYSTEM,
            category=Notification.BACKGROUND_CHECK,
            title='Background Check Request Received',
            message=f'Your background check request for {instance.name} has been received and is being processed.',
            related_object_type='Request',
            related_object_id=instance.id,
            push_sent=False
        )
        
        # Send push notification to user
        try:
            result = send_notification_to_user(
                instance.user,
                'Background Check Request Received',
                f'Your background check request for {instance.name} has been received.',
                notification_type='background_check',
                data={
                    'request_id': str(instance.id),
                    'type': 'request_received'
                }
            )
            
            if result.get('success_count', 0) > 0:
                user_notification.push_sent = True
                user_notification.push_sent_at = timezone.now()
                user_notification.save()
                
        except Exception as e:
            logger.error(f"Failed to send push notification to user: {str(e)}")
    else:
        # Check if status changed
        try:
            Request = apps.get_model('background_requests', 'Request')
            old_instance = Request.objects.get(pk=instance.pk)
            if old_instance.status != instance.status:
                # Notify user about status change
                status_messages = {
                    'Pending': 'Your background check request is pending review.',
                    'In Progress': 'Your background check is now in progress.',
                    'Completed': 'Your background check has been completed!',
                }
                
                notification = Notification.objects.create(
                    recipient=instance.user,
                    sender=None,  # System notification
                    type=Notification.ADMIN_TO_USER,
                    category=Notification.BACKGROUND_CHECK,
                    title=f'Background Check Status: {instance.status}',
                    message=status_messages.get(
                        instance.status,
                        f'Your background check status has been updated to: {instance.status}'
                    ),
                    related_object_type='Request',
                    related_object_id=instance.id,
                    push_sent=False
                )
                
                # Send push notification to user
                try:
                    result = send_notification_to_user(
                        instance.user,
                        f'Background Check Status: {instance.status}',
                        status_messages.get(instance.status, f'Status updated to: {instance.status}'),
                        notification_type='background_check',
                        data={
                            'request_id': str(instance.id),
                            'status': instance.status,
                            'type': 'status_update'
                        }
                    )
                    
                    if result.get('success_count', 0) > 0:
                        notification.push_sent = True
                        notification.push_sent_at = timezone.now()
                        notification.save()
                        
                except Exception as e:
                    logger.error(f"Failed to send status update push notification: {str(e)}")
        except Exception as e:
            logger.error(f"Error checking status change: {str(e)}")


@receiver(post_save, sender='background_requests.Report')
def notify_on_report_generated(sender, instance, created, **kwargs):
    """
    Send notification when a report is generated
    """
    if created:
        # Notify user that their report is ready
        notification = Notification.objects.create(
            recipient=instance.request.user,
            sender=None,  # System notification
            type=Notification.ADMIN_TO_USER,
            category=Notification.REPORT,
            title='Background Check Report Ready',
            message=f'Your background check report for {instance.request.name} is now available for download.',
            related_object_type='Report',
            related_object_id=instance.id,
            action_url=f'/api/reports/{instance.id}/download/',
            push_sent=False
        )
        
        # Send push notification to user
        try:
            result = send_notification_to_user(
                instance.request.user,
                'Background Check Report Ready',
                f'Your background check report for {instance.request.name} is now available.',
                notification_type='report',
                data={
                    'report_id': str(instance.id),
                    'request_id': str(instance.request.id),
                    'type': 'report_ready'
                }
            )
            
            if result.get('success_count', 0) > 0:
                notification.push_sent = True
                notification.push_sent_at = timezone.now()
                notification.save()
                
        except Exception as e:
            logger.error(f"Failed to send report ready push notification: {str(e)}")


def send_admin_notification(sender_user, title, message, category=Notification.GENERAL, 
                           related_object_type=None, related_object_id=None, action_url=None,
                           send_push=True):
    """
    Helper function to send notification to all admin users
    
    Args:
        sender_user: User who triggered the notification
        title: Notification title
        message: Notification message
        category: Notification category (default: GENERAL)
        related_object_type: Type of related object (optional)
        related_object_id: ID of related object (optional)
        action_url: URL for action button (optional)
        send_push: Whether to send push notification (default: True)
    
    Returns:
        Number of notifications created
    """
    admin_users = User.objects.filter(is_staff=True)
    count = 0
    notifications = []
    
    for admin in admin_users:
        notification = Notification.objects.create(
            recipient=admin,
            sender=sender_user,
            type=Notification.USER_TO_ADMIN,
            category=category,
            title=title,
            message=message,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            action_url=action_url,
            push_sent=False
        )
        notifications.append(notification)
        count += 1
    
    # Send push notification to admins
    if send_push and notifications:
        try:
            result = send_notification_to_admins(
                title,
                message,
                notification_type=category,
                data={
                    'related_object_type': related_object_type,
                    'related_object_id': str(related_object_id) if related_object_id else None
                }
            )
            
            if result.get('success_count', 0) > 0:
                for notification in notifications:
                    notification.push_sent = True
                    notification.push_sent_at = timezone.now()
                    notification.save()
                    
        except Exception as e:
            logger.error(f"Failed to send admin push notification: {str(e)}")
    
    return count


def send_user_notification(recipient_user, title, message, category=Notification.GENERAL,
                          sender=None, related_object_type=None, related_object_id=None, 
                          action_url=None, send_push=True):
    """
    Helper function to send notification to a specific user
    
    Args:
        recipient_user: User who will receive the notification
        title: Notification title
        message: Notification message
        category: Notification category (default: GENERAL)
        sender: User who sent the notification (optional, None for system)
        related_object_type: Type of related object (optional)
        related_object_id: ID of related object (optional)
        action_url: URL for action button (optional)
        send_push: Whether to send push notification (default: True)
    
    Returns:
        Created notification instance
    """
    notification = Notification.objects.create(
        recipient=recipient_user,
        sender=sender,
        type=Notification.ADMIN_TO_USER if sender and sender.is_staff else Notification.SYSTEM,
        category=category,
        title=title,
        message=message,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
        action_url=action_url,
        push_sent=False
    )
    
    # Send push notification to user
    if send_push:
        try:
            result = send_notification_to_user(
                recipient_user,
                title,
                message,
                notification_type=category,
                data={
                    'notification_id': str(notification.id),
                    'related_object_type': related_object_type,
                    'related_object_id': str(related_object_id) if related_object_id else None
                }
            )
            
            if result.get('success_count', 0) > 0:
                notification.push_sent = True
                notification.push_sent_at = timezone.now()
                notification.save()
                
        except Exception as e:
            logger.error(f"Failed to send user push notification: {str(e)}")
    
    return notification
