from django.urls import path
from .views import AdminRequestView, AdminReportView
from .admin_views import (
    AdminDashboardStatsView, AdminRequestManagementView, AdminRequestDetailView,
    AdminStatusUpdateView, AdminBulkStatusUpdateView, AdminNoteView, 
    AdminAssignmentView, AdminUsersView
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
]
