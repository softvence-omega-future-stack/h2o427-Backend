from django.contrib import admin
from .models import Request, Report

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at', 'state']
    search_fields = ['name', 'email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'name', 'dob', 'email', 'phone_number')
        }),
        ('Location', {
            'fields': ('city', 'state')
        }),
        ('Request Status', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'request', 'request_name', 'generated_at']
    list_filter = ['generated_at']
    search_fields = ['request__name', 'request__email']
    readonly_fields = ['generated_at']
    
    def request_name(self, obj):
        return obj.request.name
    request_name.short_description = 'Client Name'
