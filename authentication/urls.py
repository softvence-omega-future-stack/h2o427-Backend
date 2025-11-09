from django.urls import path
from .views import (
    UserRegistrationView, OTPRequestView, OTPVerifyView, UserLoginView, UserLogoutView,
    UserProfileView, UserProfileUpdateView, ChangePasswordView,
    ForgotPasswordView, ResetPasswordView
)
from .page_views import register_page, login_page, logout_page

app_name = 'auth'

urlpatterns = [
    # API endpoints
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('otp-request/', OTPRequestView.as_view(), name='otp-request'),
    path('otp-verify/', OTPVerifyView.as_view(), name='otp-verify'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='user-profile-update'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('reset-password/<str:uid>/<str:token>/', ResetPasswordView.as_view(), name='reset-password-confirm'),
    
    # Template-based views
    path('register-page/', register_page, name='register-page'),
    path('login-page/', login_page, name='login-page'),
    path('logout-page/', logout_page, name='logout-page'),
]
