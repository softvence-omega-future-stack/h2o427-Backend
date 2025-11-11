from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NotificationViewSet, 
    FCMDeviceViewSet,
    all_notifications_view,
    test_notifications_view,
    test_register_device,
    test_send_notification,
    test_view_notifications,
    test_mark_read
)

# Import admin notification views
from admin_dashboard.admin_views import (
    AdminNotificationView, 
    AdminNotificationMarkReadView, 
    AdminNotificationMarkAllReadView
)

app_name = 'notifications'

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'fcm-devices', FCMDeviceViewSet, basename='fcm-device')

urlpatterns = [
    # Admin notification endpoints
    path('admin/', AdminNotificationView.as_view(), name='admin_notifications'),
    path('admin/<int:notification_id>/mark-read/', AdminNotificationMarkReadView.as_view(), name='admin_notification_mark_read'),
    path('admin/mark-all-read/', AdminNotificationMarkAllReadView.as_view(), name='admin_notification_mark_all_read'),
    
    # Simple view pages (MTV pattern) - Put these BEFORE router urls to avoid conflicts
    path('all/', all_notifications_view, name='all_notifications'),
    path('test/', test_notifications_view, name='test_notifications'),
    path('test/register/', test_register_device, name='test_register_device'),
    path('test/send/', test_send_notification, name='test_send_notification'),
    path('test/view/', test_view_notifications, name='test_view_notifications'),
    path('test/mark-read/<int:notification_id>/', test_mark_read, name='test_mark_read'),
    
    # API endpoints (router)
    path('', include(router.urls)),
]
