from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Notification, FCMDevice

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information for notification serializers"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
        read_only_fields = fields


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for listing and retrieving notifications"""
    sender_details = UserBasicSerializer(source='sender', read_only=True)
    recipient_details = UserBasicSerializer(source='recipient', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'recipient_details',
            'sender',
            'sender_details',
            'type',
            'type_display',
            'category',
            'category_display',
            'title',
            'message',
            'is_read',
            'read_at',
            'related_object_type',
            'related_object_id',
            'action_url',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'read_at']


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications"""
    
    class Meta:
        model = Notification
        fields = [
            'recipient',
            'type',
            'category',
            'title',
            'message',
            'related_object_type',
            'related_object_id',
            'action_url',
        ]
    
    def validate(self, attrs):
        """Validate notification data"""
        request = self.context.get('request')
        
        # Set sender from request user
        if request and request.user.is_authenticated:
            attrs['sender'] = request.user
            
            # Validate notification type based on sender
            notification_type = attrs.get('type')
            
            if request.user.is_staff or request.user.is_superuser:
                # Admin can send admin_to_user or system notifications
                if notification_type not in [Notification.ADMIN_TO_USER, Notification.SYSTEM]:
                    raise serializers.ValidationError({
                        'type': 'Admin can only send admin_to_user or system notifications'
                    })
            else:
                # Regular users can only send user_to_admin notifications
                if notification_type != Notification.USER_TO_ADMIN:
                    raise serializers.ValidationError({
                        'type': 'Users can only send user_to_admin notifications'
                    })
        
        return attrs


class BulkNotificationCreateSerializer(serializers.Serializer):
    """
    Serializer for creating bulk notifications to multiple users
    
    Example:
    {
        "recipient_ids": [1, 2, 3],
        "type": "admin_to_user",
        "category": "general",
        "title": "System Maintenance",
        "message": "The system will be down this Sunday."
    }
    
    To get available user IDs, call: GET /api/notifications/available-recipients/
    """
    recipient_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=True,
        allow_empty=False,
        help_text='List of user IDs to send notification to. Example: [1, 2, 3]. Get available IDs from /api/notifications/available-recipients/',
        style={'base_template': 'textarea.html'}
    )
    type = serializers.ChoiceField(
        choices=Notification.TYPE_CHOICES,
        default=Notification.ADMIN_TO_USER,
        help_text='Type of notification (admin_to_user or system)'
    )
    category = serializers.ChoiceField(
        choices=Notification.CATEGORY_CHOICES,
        default=Notification.GENERAL,
        help_text='Category: background_check, subscription, payment, report, or general'
    )
    title = serializers.CharField(
        max_length=255,
        help_text='Notification title (e.g., "System Maintenance Alert")'
    )
    message = serializers.CharField(
        help_text='Detailed notification message'
    )
    related_object_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    related_object_id = serializers.IntegerField(required=False, allow_null=True)
    action_url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_recipient_ids(self, value):
        """Validate that all recipient IDs exist"""
        if not value:
            raise serializers.ValidationError(
                'At least one recipient is required. Get available user IDs from /api/notifications/available-recipients/'
            )
        
        existing_users = User.objects.filter(id__in=value)
        existing_ids = set(existing_users.values_list('id', flat=True))
        invalid_ids = set(value) - existing_ids
        
        if invalid_ids:
            raise serializers.ValidationError(
                f'These user IDs do not exist: {list(invalid_ids)}. '
                f'Get valid user IDs from /api/notifications/available-recipients/'
            )
        
        return value
    
    def validate(self, attrs):
        """Validate that only admins can send bulk notifications"""
        request = self.context.get('request')
        
        if request and request.user.is_authenticated:
            if not (request.user.is_staff or request.user.is_superuser):
                raise serializers.ValidationError(
                    'Only admin users can send bulk notifications'
                )
        
        return attrs


class NotificationMarkReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read/unread"""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text='List of notification IDs to mark (if not provided, marks all)'
    )
    is_read = serializers.BooleanField(default=True)


class FCMDeviceSerializer(serializers.ModelSerializer):
    """Serializer for FCM device token registration"""
    
    class Meta:
        model = FCMDevice
        fields = ['id', 'registration_token', 'device_type', 'active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def validate_registration_token(self, value):
        """Validate that token is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError("Registration token cannot be empty")
        return value.strip()
    
    def create(self, validated_data):
        """Create or update FCM device token for the authenticated user"""
        user = self.context['request'].user
        token = validated_data['registration_token']
        device_type = validated_data.get('device_type', 'web')
        
        # Check if token already exists for this user
        device, created = FCMDevice.objects.update_or_create(
            user=user,
            registration_token=token,
            defaults={
                'device_type': device_type,
                'active': True
            }
        )
        
        return device
    
    def update(self, instance, validated_data):
        """Update FCM device token"""
        instance.registration_token = validated_data.get('registration_token', instance.registration_token)
        instance.device_type = validated_data.get('device_type', instance.device_type)
        instance.active = validated_data.get('active', instance.active)
        instance.save()
        return instance
