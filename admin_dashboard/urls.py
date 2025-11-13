from django.urls import path
from .views import AdminRequestView, AdminReportView
from .admin_views import (
    AdminDashboardStatsView, AdminRequestManagementView, AdminRequestDetailView,
    AdminStatusUpdateView, AdminBulkStatusUpdateView, AdminNoteView, 
    AdminAssignmentView, AdminUsersView, AdminAllUsersView, AdminUserDetailView,
    AdminReportDownloadView, AdminPlanManagementView, AdminPlanDetailView, 
    AdminPlanToggleStatusView, AdminNotificationView, AdminNotificationMarkReadView, 
    AdminNotificationMarkAllReadView, AdminPaymentHistoryView, AdminSubscriptionAnalyticsView
)

urlpatterns = [
    # Original admin views
    path('requests/', AdminRequestView.as_view(), name='admin_requests'),
    path('requests/<int:request_id>/status/', AdminRequestView.as_view(), name='admin_update_status'),
    path('reports/', AdminReportView.as_view(), name='admin_reports'),
    path('reports/upload/', AdminReportView.as_view(), name='admin_upload_report'),
    
    # Enhanced admin dashboard views
    path('dashboard/stats/', AdminDashboardStatsView.as_view(), name='admin_dashboard_stats'),
    path('dashboard/requests/', AdminRequestManagementView.as_view(), name='admin_request_management'),
    path('dashboard/requests/<int:request_id>/', AdminRequestDetailView.as_view(), name='admin_request_detail'),
    path('dashboard/requests/<int:request_id>/status/', AdminStatusUpdateView.as_view(), name='admin_status_update'),
    path('dashboard/requests/bulk-status/', AdminBulkStatusUpdateView.as_view(), name='admin_bulk_status_update'),
    path('dashboard/requests/<int:request_id>/notes/', AdminNoteView.as_view(), name='admin_notes'),
    path('dashboard/requests/<int:request_id>/assign/', AdminAssignmentView.as_view(), name='admin_assignment'),
    path('dashboard/users/', AdminUsersView.as_view(), name='admin_users'),
    
    # NEW: Report Download
    path('dashboard/requests/<int:request_id>/report/download/', AdminReportDownloadView.as_view(), name='admin_report_download'),
    
    # NEW: All Users Management
    path('dashboard/all-users/', AdminAllUsersView.as_view(), name='admin_all_users'),
    path('dashboard/all-users/<int:user_id>/', AdminUserDetailView.as_view(), name='admin_user_detail'),
    
    # NEW: Plan Management
    path('plans/', AdminPlanManagementView.as_view(), name='admin_plans'),
    path('plans/<int:plan_id>/', AdminPlanDetailView.as_view(), name='admin_plan_detail'),
    path('plans/<int:plan_id>/toggle-status/', AdminPlanToggleStatusView.as_view(), name='admin_plan_toggle_status'),
    
    # NEW: Payment & Subscription Analytics
    path('payments/', AdminPaymentHistoryView.as_view(), name='admin_payment_history'),
    path('analytics/', AdminSubscriptionAnalyticsView.as_view(), name='admin_subscription_analytics'),
]

# Notification endpoints (to be added to notifications app urls)
notification_urlpatterns = [
    path('admin/', AdminNotificationView.as_view(), name='admin_notifications'),
    path('admin/<int:notification_id>/mark-read/', AdminNotificationMarkReadView.as_view(), name='admin_notification_mark_read'),
    path('admin/mark-all-read/', AdminNotificationMarkAllReadView.as_view(), name='admin_notification_mark_all_read'),
]
