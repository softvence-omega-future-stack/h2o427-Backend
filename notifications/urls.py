from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, FCMDeviceViewSet

app_name = 'notifications'

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'fcm-devices', FCMDeviceViewSet, basename='fcm-device')

urlpatterns = [
    path('', include(router.urls)),
]
