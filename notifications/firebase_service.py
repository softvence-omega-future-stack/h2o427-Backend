"""
Firebase Cloud Messaging (FCM) Service
Handles push notification sending via Firebase Admin SDK
"""
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from django.utils import timezone
import logging
import os

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase():
    """
    Initialize Firebase Admin SDK with service account credentials
    """
    if not firebase_admin._apps:
        try:
            # Get the path to Firebase service account JSON file
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
            
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                logger.warning("Firebase credentials file not found. Push notifications will not work.")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
    return firebase_admin._apps


def send_push_notification(device_tokens, title, body, data=None, image_url=None):
    """
    Send push notification to one or more devices
    
    Args:
        device_tokens (str or list): Single token or list of FCM device tokens
        title (str): Notification title
        body (str): Notification body
        data (dict): Additional data payload
        image_url (str): Optional image URL for rich notification
    
    Returns:
        dict: Response with success count, failure count, and failed tokens
    """
    initialize_firebase()
    
    # Convert single token to list
    if isinstance(device_tokens, str):
        device_tokens = [device_tokens]
    
    # Filter out empty tokens
    device_tokens = [token for token in device_tokens if token]
    
    if not device_tokens:
        logger.warning("No valid device tokens provided")
        return {
            'success_count': 0,
            'failure_count': 0,
            'failed_tokens': []
        }
    
    # Prepare data payload
    if data is None:
        data = {}
    
    # Add timestamp to data
    data['timestamp'] = str(timezone.now().isoformat())
    
    # Convert all data values to strings (FCM requirement)
    data = {k: str(v) for k, v in data.items()}
    
    success_count = 0
    failure_count = 0
    failed_tokens = []
    
    # Send notification to each token individually using v1 API
    for token in device_tokens:
        try:
            # Prepare notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url if image_url else None
            )
            
            # Create message for single device (v1 API)
            message = messaging.Message(
                notification=notification,
                data=data,
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        color='#4CAF50',
                        channel_id='background_check_notifications'
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                            content_available=True
                        )
                    )
                ),
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        icon='/static/icons/notification-icon.png',
                        badge='/static/icons/badge-icon.png'
                    )
                )
            )
            
            # Send the message (v1 API)
            response = messaging.send(message)
            logger.info(f"Successfully sent notification: {response}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"Failed to send notification to token {token[:50]}...: {str(e)}")
            failure_count += 1
            failed_tokens.append({
                'token': token,
                'error': str(e)
            })
    
    # Log results
    logger.info(f"Push notification summary: {success_count} succeeded, {failure_count} failed")
    
    return {
        'success_count': success_count,
        'failure_count': failure_count,
        'failed_tokens': failed_tokens
    }


def send_notification_to_user(user, title, body, notification_type='general', data=None, image_url=None):
    """
    Send push notification to all active devices of a user
    
    Args:
        user: User instance
        title (str): Notification title
        body (str): Notification body
        notification_type (str): Type of notification (for categorization)
        data (dict): Additional data payload
        image_url (str): Optional image URL
    
    Returns:
        dict: Response with success/failure counts
    """
    from .models import FCMDevice
    
    # Get all active device tokens for the user
    devices = FCMDevice.objects.filter(user=user, active=True)
    
    if not devices.exists():
        logger.info(f"No active devices found for user {user.id}")
        return {
            'success_count': 0,
            'failure_count': 0,
            'failed_tokens': [],
            'message': 'No active devices'
        }
    
    device_tokens = list(devices.values_list('registration_token', flat=True))
    
    # Add notification type to data
    if data is None:
        data = {}
    data['notification_type'] = notification_type
    data['user_id'] = str(user.id)
    
    # Send push notification
    result = send_push_notification(device_tokens, title, body, data, image_url)
    
    # Deactivate failed tokens
    if result['failed_tokens']:
        failed_token_strings = [ft['token'] for ft in result['failed_tokens']]
        FCMDevice.objects.filter(
            registration_token__in=failed_token_strings
        ).update(active=False)
        logger.info(f"Deactivated {len(failed_token_strings)} invalid tokens")
    
    return result


def send_notification_to_admins(title, body, notification_type='general', data=None, image_url=None):
    """
    Send push notification to all admin users
    
    Args:
        title (str): Notification title
        body (str): Notification body
        notification_type (str): Type of notification
        data (dict): Additional data payload
        image_url (str): Optional image URL
    
    Returns:
        dict: Response with success/failure counts
    """
    from authentication.models import User
    from .models import FCMDevice
    
    # Get all admin users
    admin_users = User.objects.filter(is_staff=True, is_active=True)
    
    if not admin_users.exists():
        logger.warning("No admin users found")
        return {
            'success_count': 0,
            'failure_count': 0,
            'failed_tokens': [],
            'message': 'No admin users'
        }
    
    # Get all active devices for admin users
    devices = FCMDevice.objects.filter(user__in=admin_users, active=True)
    
    if not devices.exists():
        logger.info("No active devices found for admin users")
        return {
            'success_count': 0,
            'failure_count': 0,
            'failed_tokens': [],
            'message': 'No active admin devices'
        }
    
    device_tokens = list(devices.values_list('registration_token', flat=True))
    
    # Add notification type to data
    if data is None:
        data = {}
    data['notification_type'] = notification_type
    data['recipient'] = 'admins'
    
    # Send push notification
    result = send_push_notification(device_tokens, title, body, data, image_url)
    
    # Deactivate failed tokens
    if result['failed_tokens']:
        failed_token_strings = [ft['token'] for ft in result['failed_tokens']]
        FCMDevice.objects.filter(
            registration_token__in=failed_token_strings
        ).update(active=False)
    
    return result


def send_topic_notification(topic, title, body, data=None, image_url=None):
    """
    Send push notification to a topic (for broadcast messages)
    
    Args:
        topic (str): Topic name (e.g., 'all_users', 'admins')
        title (str): Notification title
        body (str): Notification body
        data (dict): Additional data payload
        image_url (str): Optional image URL
    
    Returns:
        str: Message ID if successful
    """
    initialize_firebase()
    
    try:
        # Prepare notification
        notification = messaging.Notification(
            title=title,
            body=body,
            image=image_url if image_url else None
        )
        
        # Prepare data payload
        if data is None:
            data = {}
        data['timestamp'] = str(timezone.now().isoformat())
        
        # Create message for topic
        message = messaging.Message(
            notification=notification,
            data=data,
            topic=topic,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    color='#4CAF50'
                )
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1
                    )
                )
            )
        )
        
        # Send the message
        response = messaging.send(message)
        logger.info(f"Successfully sent message to topic '{topic}': {response}")
        
        return {'message_id': response, 'success': True}
    
    except Exception as e:
        logger.error(f"Error sending topic notification: {str(e)}")
        return {'success': False, 'error': str(e)}


def subscribe_to_topic(device_tokens, topic):
    """
    Subscribe device tokens to a topic
    
    Args:
        device_tokens (str or list): Single token or list of tokens
        topic (str): Topic name
    
    Returns:
        dict: Response with success/failure counts
    """
    initialize_firebase()
    
    if isinstance(device_tokens, str):
        device_tokens = [device_tokens]
    
    try:
        response = messaging.subscribe_to_topic(device_tokens, topic)
        logger.info(f"Subscribed {response.success_count} devices to topic '{topic}'")
        return {
            'success_count': response.success_count,
            'failure_count': response.failure_count
        }
    except Exception as e:
        logger.error(f"Error subscribing to topic: {str(e)}")
        return {
            'success_count': 0,
            'failure_count': len(device_tokens),
            'error': str(e)
        }


def unsubscribe_from_topic(device_tokens, topic):
    """
    Unsubscribe device tokens from a topic
    
    Args:
        device_tokens (str or list): Single token or list of tokens
        topic (str): Topic name
    
    Returns:
        dict: Response with success/failure counts
    """
    initialize_firebase()
    
    if isinstance(device_tokens, str):
        device_tokens = [device_tokens]
    
    try:
        response = messaging.unsubscribe_from_topic(device_tokens, topic)
        logger.info(f"Unsubscribed {response.success_count} devices from topic '{topic}'")
        return {
            'success_count': response.success_count,
            'failure_count': response.failure_count
        }
    except Exception as e:
        logger.error(f"Error unsubscribing from topic: {str(e)}")
        return {
            'success_count': 0,
            'failure_count': len(device_tokens),
            'error': str(e)
        }
