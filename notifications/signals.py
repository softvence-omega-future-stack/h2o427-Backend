from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.apps import apps
from .models import Notification

User = get_user_model()


@receiver(post_save, sender='background_requests.Request')
def notify_on_request_status_change(sender, instance, created, **kwargs):
    """
    Send notification when background check request status changes
    """
    if created:
        # Notify all admins when a new request is submitted
        admin_users = User.objects.filter(is_staff=True)
        
        for admin in admin_users:
            Notification.objects.create(
                recipient=admin,
                sender=instance.user,
                type=Notification.USER_TO_ADMIN,
                category=Notification.BACKGROUND_CHECK,
                title='New Background Check Request',
                message=f'{instance.user.username} has submitted a new background check request for {instance.name}.',
                related_object_type='Request',
                related_object_id=instance.id,
                action_url=f'/admin/background_requests/request/{instance.id}/change/'
            )
        
        # Notify user that their request was received
        Notification.objects.create(
            recipient=instance.user,
            sender=None,  # System notification
            type=Notification.SYSTEM,
            category=Notification.BACKGROUND_CHECK,
            title='Background Check Request Received',
            message=f'Your background check request for {instance.name} has been received and is being processed.',
            related_object_type='Request',
            related_object_id=instance.id,
        )
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
                
                Notification.objects.create(
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
                )
        except Exception:
            pass


@receiver(post_save, sender='background_requests.Report')
def notify_on_report_generated(sender, instance, created, **kwargs):
    """
    Send notification when a report is generated
    """
    if created:
        # Notify user that their report is ready
        Notification.objects.create(
            recipient=instance.request.user,
            sender=None,  # System notification
            type=Notification.ADMIN_TO_USER,
            category=Notification.REPORT,
            title='Background Check Report Ready',
            message=f'Your background check report for {instance.request.name} is now available for download.',
            related_object_type='Report',
            related_object_id=instance.id,
            action_url=f'/api/reports/{instance.id}/download/'
        )


def send_admin_notification(sender_user, title, message, category=Notification.GENERAL, 
                           related_object_type=None, related_object_id=None, action_url=None):
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
    
    Returns:
        Number of notifications created
    """
    admin_users = User.objects.filter(is_staff=True)
    count = 0
    
    for admin in admin_users:
        Notification.objects.create(
            recipient=admin,
            sender=sender_user,
            type=Notification.USER_TO_ADMIN,
            category=category,
            title=title,
            message=message,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
            action_url=action_url
        )
        count += 1
    
    return count


def send_user_notification(recipient_user, title, message, category=Notification.GENERAL,
                          sender=None, related_object_type=None, related_object_id=None, 
                          action_url=None):
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
        action_url=action_url
    )
    
    return notification
