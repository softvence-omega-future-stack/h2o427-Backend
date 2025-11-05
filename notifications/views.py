from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.contrib.auth import get_user_model
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
