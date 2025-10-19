from django.db import models
from django.contrib.auth import get_user_model
from requests.models import Request

User = get_user_model()

class AdminDashboardSettings(models.Model):
    """Model to store admin dashboard configuration settings"""
    admin_user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    notifications_enabled = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    auto_assign_requests = models.BooleanField(default=False)
    default_status_filter = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Requests'),
            ('pending', 'Pending Only'),
            ('in_progress', 'In Progress Only'),
            ('completed', 'Completed Only'),
        ],
        default='all'
    )
    requests_per_page = models.IntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Admin Dashboard Setting"
        verbose_name_plural = "Admin Dashboard Settings"

    def __str__(self):
        return f"Dashboard Settings for {self.admin_user.username}"

class RequestActivity(models.Model):
    """Model to track activities/actions performed on requests"""
    ACTIVITY_TYPES = [
        ('status_change', 'Status Changed'),
        ('comment_added', 'Comment Added'),
        ('report_uploaded', 'Report Uploaded'),
        ('request_assigned', 'Request Assigned'),
        ('request_created', 'Request Created'),
        ('report_downloaded', 'Report Downloaded'),
    ]

    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='activities')
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    old_value = models.CharField(max_length=255, blank=True, null=True)
    new_value = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Request Activity"
        verbose_name_plural = "Request Activities"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.activity_type} on {self.request.name} by {self.admin_user.username}"

class AdminNote(models.Model):
    """Model for admin notes on specific requests"""
    request = models.ForeignKey(Request, on_delete=models.CASCADE, related_name='admin_notes')
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'is_staff': True})
    note = models.TextField()
    is_internal = models.BooleanField(default=True, help_text="Internal notes are not visible to clients")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Admin Note"
        verbose_name_plural = "Admin Notes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.request.name} by {self.admin_user.username}"

class RequestAssignment(models.Model):
    """Model to track request assignments to specific admins"""
    request = models.OneToOneField(Request, on_delete=models.CASCADE, related_name='assignment')
    assigned_to = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'is_staff': True},
        related_name='assigned_requests'
    )
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'is_staff': True},
        related_name='assignments_made'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(blank=True, null=True)
    priority = models.CharField(
        max_length=10,
        choices=[
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='medium'
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Request Assignment"
        verbose_name_plural = "Request Assignments"

    def __str__(self):
        return f"{self.request.name} assigned to {self.assigned_to.username}"
