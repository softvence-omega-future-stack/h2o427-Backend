from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RequestViewSet, ReportViewSet, submit_request_view, request_success_view

app_name = 'requests'

router = DefaultRouter()
router.register(r'api', RequestViewSet, basename='api')
router.register(r'reports', ReportViewSet, basename='reports')

urlpatterns = [
    # Template-based views
    path('submit/', submit_request_view, name='submit_request'),
    path('success/<int:request_id>/', request_success_view, name='request_success'),
    
    # API endpoints
    path('', include(router.urls)),
]
