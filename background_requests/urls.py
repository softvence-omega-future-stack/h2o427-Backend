from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RequestViewSet, ReportViewSet

router = DefaultRouter()
router.register(r'', RequestViewSet, basename='requests')
router.register(r'reports', ReportViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
]
