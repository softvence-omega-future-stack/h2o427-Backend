from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegisterView, LoginView, UserProfileView, UserViewSet

# Create router for viewsets
router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    
    # Include router URLs for user management
    path('', include(router.urls)),
]
