from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RequestViewSet, ReportViewSet, submit_request_view, request_success_view, payment_success_view, payment_cancelled_view
from .page_views import submit_request_page, request_success_page, view_report_page

app_name = 'requests'

router = DefaultRouter()
router.register(r'api', RequestViewSet, basename='api')
router.register(r'reports', ReportViewSet, basename='reports')

urlpatterns = [
    # Template-based views (existing)
    path('submit/', submit_request_view, name='submit_request'),
    path('success/<int:request_id>/', request_success_view, name='request_success'),
    
    # Payment success/cancel pages (MTV pattern - simple UI)
    path('payment-success/', payment_success_view, name='payment-success'),
    path('payment-cancelled/', payment_cancelled_view, name='payment-cancelled'),
    
    # New simple UI template views
    path('submit-page/', submit_request_page, name='submit-page'),
    path('request-success/<int:request_id>/', request_success_page, name='request-success'),
    path('view-report/<int:request_id>/', view_report_page, name='view-report'),
    
    # API endpoints
    path('', include(router.urls)),
]
