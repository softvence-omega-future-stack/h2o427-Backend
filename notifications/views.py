from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Notification, FCMDevice
from .serializers import (
    NotificationSerializer,
    NotificationCreateSerializer,
    BulkNotificationCreateSerializer,
    NotificationMarkReadSerializer,
    FCMDeviceSerializer
)

User = get_user_model()


class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing notifications
    
    Provides CRUD operations for notifications with the following features:
    - List notifications (filtered by user role)
    - Create single notification
    - Create bulk notifications (admin only)
    - Mark notifications as read/unread
    - Get unread count
    - Delete notifications
    """
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    filterset_fields = ['type', 'category', 'is_read']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter notifications based on user role
        - Admin: sees all notifications
        - Regular users: see only their own notifications
        """
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
            
        user = self.request.user
        
        if user.is_staff or user.is_superuser:
            # Admin can see all notifications
            queryset = Notification.objects.all()
        else:
            # Regular users see only their notifications
            queryset = Notification.objects.filter(recipient=user)
        
        # Optional filter by type
        notification_type = self.request.query_params.get('type', None)
        if notification_type:
            queryset = queryset.filter(type=notification_type)
        
        # Optional filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        # Optional filter by read status
        is_read = self.request.query_params.get('is_read', None)
        if is_read is not None:
            is_read_bool = is_read.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_read=is_read_bool)
        
        return queryset.select_related('sender', 'recipient')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return NotificationCreateSerializer
        elif self.action == 'bulk_create':
            return BulkNotificationCreateSerializer
        elif self.action == 'mark_as_read':
            return NotificationMarkReadSerializer
        return NotificationSerializer
    
    @swagger_auto_schema(
        operation_description="Get list of notifications for the authenticated user",
        responses={200: NotificationSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """List notifications"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new notification",
        request_body=NotificationCreateSerializer,
        responses={
            201: NotificationSerializer,
            400: 'Bad Request'
        }
    )
    def create(self, request, *args, **kwargs):
        """Create a single notification"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = serializer.save()
        
        output_serializer = NotificationSerializer(notification)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="""
        Create bulk notifications to multiple users (Admin only)
        
        **Example Request:**
        ```json
        {
            "recipient_ids": [1, 2, 3],
            "type": "admin_to_user",
            "category": "general",
            "title": "System Maintenance Alert",
            "message": "The system will be under maintenance this Sunday from 2 AM to 6 AM."
        }
        ```
        
        **Note:** You must provide `recipient_ids` as an array of user IDs.
        """,
        request_body=BulkNotificationCreateSerializer,
        responses={
            201: openapi.Response(
                description="Notifications created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, example='Successfully created 3 notifications'),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER, example=3),
                    }
                )
            ),
            400: 'Bad Request - Missing required fields',
            403: 'Forbidden - Admin only'
        }
    )
    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request):
        """
        Create notifications for multiple users at once (Admin only)
        
        This endpoint allows administrators to send the same notification
        to multiple users efficiently.
        
        Required fields:
        - recipient_ids: List of user IDs (e.g., [1, 2, 3])
        - title: Notification title
        - message: Notification message
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        recipient_ids = serializer.validated_data.pop('recipient_ids')
        
        # Create notifications for all recipients
        notifications = []
        for recipient_id in recipient_ids:
            notification = Notification.objects.create(
                recipient_id=recipient_id,
                sender=request.user,
                **serializer.validated_data
            )
            notifications.append(notification)
        
        return Response({
            'message': f'Successfully created {len(notifications)} notifications',
            'count': len(notifications)
        }, status=status.HTTP_201_CREATED)
    
    @swagger_auto_schema(
        operation_description="Get list of available users for sending bulk notifications (Admin only)",
        responses={
            200: openapi.Response(
                description="List of available users",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_users': openapi.Schema(type=openapi.TYPE_INTEGER, example=10),
                        'users': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                                    'username': openapi.Schema(type=openapi.TYPE_STRING, example='john_doe'),
                                    'email': openapi.Schema(type=openapi.TYPE_STRING, example='john@example.com'),
                                    'full_name': openapi.Schema(type=openapi.TYPE_STRING, example='John Doe'),
                                    'is_staff': openapi.Schema(type=openapi.TYPE_BOOLEAN, example=False),
                                }
                            )
                        ),
                        'example_request': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            example={
                                'recipient_ids': [1, 2, 3],
                                'type': 'admin_to_user',
                                'category': 'general',
                                'title': 'System Update',
                                'message': 'New features available'
                            }
                        )
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='available-recipients', permission_classes=[IsAuthenticated])
    def available_recipients(self, request):
        """
        Get list of users available for bulk notifications
        
        Returns all users with their IDs, which you can use in the bulk-create endpoint.
        Also provides an example request body for bulk-create.
        """
        users = User.objects.all().values('id', 'username', 'email', 'full_name', 'is_staff')
        users_list = list(users)
        
        # Create example with actual user IDs
        user_ids = [user['id'] for user in users_list[:3]] if users_list else [1, 2, 3]
        
        return Response({
            'total_users': len(users_list),
            'users': users_list,
            'example_bulk_create_request': {
                'recipient_ids': user_ids,
                'type': 'admin_to_user',
                'category': 'general',
                'title': 'System Update',
                'message': 'New features are now available. Please check them out!'
            },
            'instructions': 'Copy the recipient_ids from the users list above and use them in /api/notifications/bulk-create/'
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Mark notifications as read or unread",
        request_body=NotificationMarkReadSerializer,
        responses={
            200: openapi.Response(
                description="Notifications marked successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            400: 'Bad Request'
        }
    )
    @action(detail=False, methods=['post'], url_path='mark-read')
    def mark_as_read(self, request):
        """
        Mark one or more notifications as read/unread
        
        If notification_ids is not provided, marks all user's notifications.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification_ids = serializer.validated_data.get('notification_ids')
        is_read = serializer.validated_data.get('is_read', True)
        
        # Get base queryset (user's notifications)
        queryset = self.get_queryset()
        
        # Filter by specific IDs if provided
        if notification_ids:
            queryset = queryset.filter(id__in=notification_ids)
        
        # Update notifications
        if is_read:
            count = 0
            for notification in queryset.filter(is_read=False):
                notification.mark_as_read()
                count += 1
        else:
            count = 0
            for notification in queryset.filter(is_read=True):
                notification.mark_as_unread()
                count += 1
        
        action_text = 'read' if is_read else 'unread'
        return Response({
            'message': f'Successfully marked {count} notifications as {action_text}',
            'count': count
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Get count of unread notifications",
        responses={
            200: openapi.Response(
                description="Unread notification count",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'unread_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get count of unread notifications for the current user"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count}, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Mark all notifications as read",
        responses={
            200: openapi.Response(
                description="All notifications marked as read",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read for the current user"""
        count = 0
        for notification in self.get_queryset().filter(is_read=False):
            notification.mark_as_read()
            count += 1
        
        return Response({
            'message': f'Successfully marked {count} notifications as read',
            'count': count
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Delete all read notifications",
        responses={
            200: openapi.Response(
                description="Read notifications deleted",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['delete'], url_path='clear-read')
    def clear_read(self, request):
        """Delete all read notifications for the current user"""
        queryset = self.get_queryset().filter(is_read=True)
        count = queryset.count()
        queryset.delete()
        
        return Response({
            'message': f'Successfully deleted {count} read notifications',
            'count': count
        }, status=status.HTTP_200_OK)


class FCMDeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing FCM device tokens
    
    Provides endpoints for:
    - Register device token
    - Update device token  
    - List user's devices
    - Delete device token
    """
    permission_classes = [IsAuthenticated]
    serializer_class = FCMDeviceSerializer
    
    def get_queryset(self):
        """Return only the authenticated user's devices"""
        if getattr(self, 'swagger_fake_view', False):
            return FCMDevice.objects.none()
        return FCMDevice.objects.filter(user=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Register or update FCM device token for push notifications",
        request_body=FCMDeviceSerializer,
        responses={
            201: FCMDeviceSerializer,
            400: 'Bad Request'
        }
    )
    def create(self, request, *args, **kwargs):
        """
        Register a new FCM device token
        
        If token already exists for this user, it will be updated.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()
        
        return Response(
            FCMDeviceSerializer(device).data,
            status=status.HTTP_201_CREATED
        )
    
    @swagger_auto_schema(
        operation_description="Get all FCM devices registered for the authenticated user",
        responses={200: FCMDeviceSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        """List all devices for the authenticated user"""
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Delete FCM device token (unregister device)",
        responses={
            204: 'Device token deleted successfully',
            404: 'Device not found'
        }
    )
    def destroy(self, request, *args, **kwargs):
        """Delete a device token (unregister)"""
        return super().destroy(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Deactivate all devices for the authenticated user",
        responses={
            200: openapi.Response(
                description="All devices deactivated",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            )
        }
    )
    @action(detail=False, methods=['post'], url_path='deactivate-all')
    def deactivate_all(self, request):
        """Deactivate all devices for the current user"""
        count = self.get_queryset().filter(active=True).update(active=False)
        return Response({
            'message': f'Successfully deactivated {count} devices',
            'count': count
        }, status=status.HTTP_200_OK)


# ==================== Test Views (MTV Pattern) ====================
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods


def all_notifications_view(request):
    """View all notifications and devices - simple overview page"""
    # Get all notifications
    all_notifications = Notification.objects.all().order_by('-created_at')[:50]
    
    # Get all devices
    all_devices = FCMDevice.objects.all().order_by('-created_at')[:50]
    
    # Get all users for quick reference
    users = User.objects.all().values('id', 'username', 'email')[:20]
    
    context = {
        'all_notifications': all_notifications,
        'all_devices': all_devices,
        'users': users,
    }
    return render(request, 'notifications/all_notifications.html', context)


def test_notifications_view(request):
    """Main test page for notification system"""
    notifications = None
    devices = FCMDevice.objects.all().order_by('-created_at')[:20]
    
    # Get notifications if user_id is provided
    if request.GET.get('user_id'):
        user_id = request.GET.get('user_id')
        notifications = Notification.objects.filter(recipient_id=user_id).order_by('-created_at')
    
    context = {
        'notifications': notifications,
        'devices': devices,
    }
    return render(request, 'notifications/test_notifications.html', context)


@require_http_methods(["POST"])
def test_register_device(request):
    """Register a device token"""
    try:
        user_id = request.POST.get('user_id')
        device_token = request.POST.get('device_token')
        device_type = request.POST.get('device_type', 'android')
        
        # Get or create user
        user = User.objects.get(id=user_id)
        
        # Create or update device
        device, created = FCMDevice.objects.update_or_create(
            user=user,
            registration_token=device_token,
            defaults={
                'device_type': device_type,
                'active': True
            }
        )
        
        if created:
            messages.success(request, f'Device token registered successfully for User ID: {user_id}')
        else:
            messages.success(request, f'Device token updated successfully for User ID: {user_id}')
            
    except User.DoesNotExist:
        messages.error(request, f'User with ID {user_id} does not exist')
    except Exception as e:
        messages.error(request, f'Error registering device: {str(e)}')
    
    return redirect('notifications:test_notifications')


@require_http_methods(["POST"])
def test_send_notification(request):
    """Send a test notification"""
    try:
        user_id = request.POST.get('user_id')
        title = request.POST.get('title')
        message_text = request.POST.get('message')
        notification_type = request.POST.get('notification_type', 'general')
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Map notification_type to model fields
        type_mapping = {
            'general': Notification.SYSTEM,
            'request_update': Notification.ADMIN_TO_USER,
            'report_ready': Notification.ADMIN_TO_USER,
            'subscription': Notification.SYSTEM,
            'admin': Notification.ADMIN_TO_USER,
        }
        
        category_mapping = {
            'general': Notification.GENERAL,
            'request_update': Notification.BACKGROUND_CHECK,
            'report_ready': Notification.REPORT,
            'subscription': Notification.SUBSCRIPTION,
            'admin': Notification.GENERAL,
        }
        
        # Create notification
        notification = Notification.objects.create(
            recipient=user,
            title=title,
            message=message_text,
            type=type_mapping.get(notification_type, Notification.SYSTEM),
            category=category_mapping.get(notification_type, Notification.GENERAL),
            sender=None  # System notification
        )
        
        # Try to send push notification using the correct function
        from .firebase_service import send_notification_to_user
        result = send_notification_to_user(
            user=user,
            title=title,
            body=message_text,
            notification_type=notification_type,
            data={'notification_id': str(notification.id)}
        )
        
        if result.get('success_count', 0) > 0:
            # Update notification record
            notification.push_sent = True
            notification.push_sent_at = timezone.now()
            notification.save(update_fields=['push_sent', 'push_sent_at'])
            
            messages.success(request, f'Notification sent successfully to User ID: {user_id}. Push sent to {result.get("success_count", 0)} devices.')
        elif result.get('message'):
            messages.warning(request, f'Notification created but {result.get("message")}')
        else:
            notification.push_error = f"Failed: {result.get('failure_count', 0)} devices failed"
            notification.save(update_fields=['push_error'])
            messages.warning(request, f'Notification created but push failed to {result.get("failure_count", 0)} devices')
            
    except User.DoesNotExist:
        messages.error(request, f'User with ID {user_id} does not exist')
    except Exception as e:
        messages.error(request, f'Error sending notification: {str(e)}')
    
    return redirect('notifications:test_notifications')


def test_view_notifications(request):
    """View notifications for a user"""
    user_id = request.GET.get('user_id')
    
    if not user_id:
        messages.error(request, 'User ID is required')
        return redirect('notifications:test_notifications')
    
    return redirect(f'/notifications/test/?user_id={user_id}')


@require_http_methods(["POST"])
def test_mark_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = Notification.objects.get(id=notification_id)
        notification.mark_as_read()
        messages.success(request, f'Notification {notification_id} marked as read')
    except Notification.DoesNotExist:
        messages.error(request, f'Notification {notification_id} not found')
    except Exception as e:
        messages.error(request, f'Error marking notification as read: {str(e)}')
    
    # Redirect back to the page with the user_id filter
    user_id = request.POST.get('user_id') or notification.recipient_id
    return redirect(f'/notifications/test/?user_id={user_id}')
