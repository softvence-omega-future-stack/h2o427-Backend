from django.contrib import admin
from requests.models import Request, Report
from .models import AdminDashboardSettings, RequestActivity, AdminNote, RequestAssignment

@admin.register(AdminDashboardSettings)
class AdminDashboardSettingsAdmin(admin.ModelAdmin):
    list_display = ['admin_user', 'notifications_enabled', 'email_notifications', 'default_status_filter', 'requests_per_page']
    list_filter = ['notifications_enabled', 'email_notifications', 'auto_assign_requests']
    search_fields = ['admin_user__username', 'admin_user__email']

@admin.register(RequestActivity)
class RequestActivityAdmin(admin.ModelAdmin):
    list_display = ['request', 'admin_user', 'activity_type', 'timestamp']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['request__name', 'admin_user__username', 'description']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']

@admin.register(AdminNote)
class AdminNoteAdmin(admin.ModelAdmin):
    list_display = ['request', 'admin_user', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['request__name', 'admin_user__username', 'note']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(RequestAssignment)
class RequestAssignmentAdmin(admin.ModelAdmin):
    list_display = ['request', 'assigned_to', 'assigned_by', 'priority', 'assigned_at']
    list_filter = ['priority', 'assigned_at']
    search_fields = ['request__name', 'assigned_to__username', 'assigned_by__username']
    readonly_fields = ['assigned_at']

# The Request and Report models are already registered in the requests app
# This file can be used for custom admin views or dashboard-specific admin configurations
