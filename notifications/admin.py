from django.contrib import admin
from django.utils.html import format_html
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for managing notifications"""
    
    list_display = [
        'id',
        'title',
        'recipient_link',
        'sender_link',
        'type_badge',
        'category_badge',
        'is_read_icon',
        'created_at',
    ]
    
    list_filter = [
        'type',
        'category',
        'is_read',
        'created_at',
    ]
    
    search_fields = [
        'title',
        'message',
        'recipient__username',
        'recipient__email',
        'sender__username',
        'sender__email',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'read_at',
    ]
    
    fieldsets = (
        ('Recipients & Sender', {
            'fields': ('recipient', 'sender')
        }),
        ('Notification Details', {
            'fields': ('type', 'category', 'title', 'message')
        }),
        ('Related Object', {
            'fields': ('related_object_type', 'related_object_id', 'action_url'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    actions = ['mark_as_read', 'mark_as_unread', 'delete_selected']
    
    def recipient_link(self, obj):
        """Display recipient with link"""
        if obj.recipient:
            return format_html(
                '<a href="/admin/authentication/user/{}/change/">{}</a>',
                obj.recipient.id,
                obj.recipient.username or obj.recipient.email
            )
        return '-'
    recipient_link.short_description = 'Recipient'
    
    def sender_link(self, obj):
        """Display sender with link"""
        if obj.sender:
            return format_html(
                '<a href="/admin/authentication/user/{}/change/">{}</a>',
                obj.sender.id,
                obj.sender.username or obj.sender.email
            )
        return 'System'
    sender_link.short_description = 'Sender'
    
    def type_badge(self, obj):
        """Display notification type with color badge"""
        colors = {
            'admin_to_user': '#17a2b8',  # info blue
            'user_to_admin': '#ffc107',  # warning yellow
            'system': '#6c757d',  # secondary gray
        }
        color = colors.get(obj.type, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_type_display()
        )
    type_badge.short_description = 'Type'
    
    def category_badge(self, obj):
        """Display notification category with color badge"""
        colors = {
            'background_check': '#007bff',  # primary blue
            'subscription': '#28a745',  # success green
            'payment': '#dc3545',  # danger red
            'report': '#fd7e14',  # orange
            'general': '#6c757d',  # gray
        }
        color = colors.get(obj.category, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_category_display()
        )
    category_badge.short_description = 'Category'
    
    def is_read_icon(self, obj):
        """Display read status with icon"""
        if obj.is_read:
            return format_html(
                '<span style="color: #28a745; font-size: 16px;" title="Read">✓</span>'
            )
        return format_html(
            '<span style="color: #dc3545; font-size: 16px;" title="Unread">✗</span>'
        )
    is_read_icon.short_description = 'Read'
    
    def mark_as_read(self, request, queryset):
        """Bulk action to mark notifications as read"""
        count = 0
        for notification in queryset:
            if not notification.is_read:
                notification.mark_as_read()
                count += 1
        self.message_user(request, f'{count} notification(s) marked as read.')
    mark_as_read.short_description = 'Mark selected as read'
    
    def mark_as_unread(self, request, queryset):
        """Bulk action to mark notifications as unread"""
        count = 0
        for notification in queryset:
            if notification.is_read:
                notification.mark_as_unread()
                count += 1
        self.message_user(request, f'{count} notification(s) marked as unread.')
    mark_as_unread.short_description = 'Mark selected as unread'
