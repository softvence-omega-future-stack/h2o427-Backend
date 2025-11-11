from rest_framework import serializers
from django.contrib.auth import get_user_model
from background_requests.models import Request, Report
from .models import AdminDashboardSettings, RequestActivity, AdminNote, RequestAssignment

User = get_user_model()

class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer for admin users with additional admin-specific fields"""
    full_name = serializers.SerializerMethodField()
    assigned_requests_count = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 
                 'is_staff', 'is_superuser', 'date_joined', 'assigned_requests_count']
        read_only_fields = ['id', 'date_joined', 'assigned_requests_count']
    
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_assigned_requests_count(self, obj):
        if hasattr(obj, 'assigned_requests'):
            return obj.assigned_requests.count()
        return 0

class AdminRequestSerializer(serializers.ModelSerializer):
    """Enhanced request serializer for admin dashboard with additional fields"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_full_name = serializers.SerializerMethodField()
    assigned_to = serializers.SerializerMethodField()
    activity_count = serializers.SerializerMethodField()
    latest_activity = serializers.SerializerMethodField()
    has_report = serializers.SerializerMethodField()
    priority = serializers.SerializerMethodField()
    
    class Meta:
        model = Request
        fields = ['id', 'user', 'user_name', 'user_full_name', 'name', 'dob', 'city', 'state', 
                 'email', 'phone_number', 'status', 'created_at', 'updated_at', 'assigned_to',
                 'activity_count', 'latest_activity', 'has_report', 'priority']
        read_only_fields = ['user', 'created_at', 'updated_at', 'assigned_to', 
                           'activity_count', 'latest_activity', 'has_report', 'priority']
    
    def get_user_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()
    
    def get_assigned_to(self, obj):
        if hasattr(obj, 'assignment'):
            return {
                'id': obj.assignment.assigned_to.id,
                'username': obj.assignment.assigned_to.username,
                'full_name': f"{obj.assignment.assigned_to.first_name} {obj.assignment.assigned_to.last_name}".strip(),
                'priority': obj.assignment.priority,
                'due_date': obj.assignment.due_date
            }
        return None
    
    def get_activity_count(self, obj):
        return obj.activities.count() if hasattr(obj, 'activities') else 0
    
    def get_latest_activity(self, obj):
        if hasattr(obj, 'activities') and obj.activities.exists():
            latest = obj.activities.first()
            return {
                'type': latest.activity_type,
                'description': latest.description,
                'timestamp': latest.timestamp,
                'admin_user': latest.admin_user.username
            }
        return None
    
    def get_has_report(self, obj):
        return hasattr(obj, 'report') and obj.report is not None
    
    def get_priority(self, obj):
        if hasattr(obj, 'assignment'):
            return obj.assignment.priority
        return 'medium'

class AdminReportSerializer(serializers.ModelSerializer):
    """Enhanced report serializer for admin dashboard"""
    request_name = serializers.CharField(source='request.name', read_only=True)
    request_status = serializers.CharField(source='request.status', read_only=True)
    client_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = ['id', 'request', 'request_name', 'request_status', 'client_name', 
                 'pdf', 'generated_at', 'notes']
        read_only_fields = ['generated_at']
    
    def get_client_name(self, obj):
        return f"{obj.request.user.first_name} {obj.request.user.last_name}".strip()

class AdminDashboardSettingsSerializer(serializers.ModelSerializer):
    """Serializer for admin dashboard settings"""
    admin_username = serializers.CharField(source='admin_user.username', read_only=True)
    
    class Meta:
        model = AdminDashboardSettings
        fields = ['id', 'admin_user', 'admin_username', 'notifications_enabled', 
                 'email_notifications', 'auto_assign_requests', 'default_status_filter',
                 'requests_per_page', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class RequestActivitySerializer(serializers.ModelSerializer):
    """Serializer for request activities"""
    admin_username = serializers.CharField(source='admin_user.username', read_only=True)
    admin_full_name = serializers.SerializerMethodField()
    request_name = serializers.CharField(source='request.name', read_only=True)
    
    class Meta:
        model = RequestActivity
        fields = ['id', 'request', 'request_name', 'admin_user', 'admin_username', 
                 'admin_full_name', 'activity_type', 'description', 'old_value', 
                 'new_value', 'timestamp']
        read_only_fields = ['timestamp']
    
    def get_admin_full_name(self, obj):
        return f"{obj.admin_user.first_name} {obj.admin_user.last_name}".strip()

class AdminNoteSerializer(serializers.ModelSerializer):
    """Serializer for admin notes"""
    admin_username = serializers.CharField(source='admin_user.username', read_only=True)
    admin_full_name = serializers.SerializerMethodField()
    request_name = serializers.CharField(source='request.name', read_only=True)
    
    class Meta:
        model = AdminNote
        fields = ['id', 'request', 'request_name', 'admin_user', 'admin_username',
                 'admin_full_name', 'note', 'is_internal', 'created_at', 'updated_at']
        read_only_fields = ['id', 'request', 'admin_user', 'request_name', 'admin_username', 
                           'admin_full_name', 'created_at', 'updated_at']
    
    def get_admin_full_name(self, obj):
        return f"{obj.admin_user.first_name} {obj.admin_user.last_name}".strip()

class RequestAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for request assignments"""
    assigned_to_username = serializers.CharField(source='assigned_to.username', read_only=True)
    assigned_to_full_name = serializers.SerializerMethodField()
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    request_name = serializers.CharField(source='request.name', read_only=True)
    
    class Meta:
        model = RequestAssignment
        fields = ['id', 'request', 'request_name', 'assigned_to', 'assigned_to_username',
                 'assigned_to_full_name', 'assigned_by', 'assigned_by_username', 
                 'assigned_at', 'due_date', 'priority', 'notes']
        read_only_fields = ['id', 'request', 'request_name', 'assigned_by', 'assigned_by_username', 
                           'assigned_to_username', 'assigned_to_full_name', 'assigned_at']
    
    def validate_assigned_to(self, value):
        """Validate that the assigned_to user exists and is a staff member"""
        if not value.is_staff:
            raise serializers.ValidationError(
                f"User '{value.username}' (ID: {value.id}) is not an admin user. "
                "Only admin users (staff members) can be assigned requests."
            )
        return value
    
    def get_assigned_to_full_name(self, obj):
        return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip()

class StatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating request status with activity logging"""
    status = serializers.ChoiceField(choices=[
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ])
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        """Normalize status to match model choices"""
        status_mapping = {
            'pending': 'Pending',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'Pending': 'Pending',
            'In Progress': 'In Progress',
            'Completed': 'Completed',
        }
        return status_mapping.get(value, value)

class BulkStatusUpdateSerializer(serializers.Serializer):
    """Serializer for bulk status updates"""
    request_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False
    )
    status = serializers.ChoiceField(choices=[
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ])
    notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_status(self, value):
        """Normalize status to match model choices"""
        status_mapping = {
            'pending': 'Pending',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'Pending': 'Pending',
            'In Progress': 'In Progress',
            'Completed': 'Completed',
        }
        return status_mapping.get(value, value)

class DashboardStatsSerializer(serializers.Serializer):
    """Serializer for dashboard statistics"""
    total_requests = serializers.IntegerField()
    pending_requests = serializers.IntegerField()
    in_progress_requests = serializers.IntegerField()
    completed_requests = serializers.IntegerField()
    total_clients = serializers.IntegerField()
    recent_requests = AdminRequestSerializer(many=True)
    recent_activities = RequestActivitySerializer(many=True)