import random
import os
from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .serializers import (
    UserRegistrationSerializer, PasswordResetSerializer,
    UserProfileSerializer, UserProfileUpdateSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
)
from .models import PhoneOTP, User
from twilio.rest import Client
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed



class UserRegistrationView(views.APIView):
    permission_classes = []  # Allow unauthenticated access
    
    @swagger_auto_schema(
        operation_description="Register a new user account",
        operation_summary="User Registration",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password', 'confirm_password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username (optional, will use email if not provided)', example='johndoe'),
                'full_name': openapi.Schema(type=openapi.TYPE_STRING, description='Full name of the user', example='John Doe'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Email address (must be unique)', example='john.doe@example.com'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number in international format', example='+1234567890'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='Password (min 8 characters)', example='SecurePass123!'),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='Confirm password', example='SecurePass123!'),
            }
        ),
        responses={
            201: openapi.Response(
                description="User registered successfully",
                examples={
                    "application/json": {
                        "message": "User registered successfully!",
                        "user": {
                            "username": "johndoe",
                            "email": "john.doe@example.com",
                            "full_name": "John Doe"
                        }
                    }
                }
            ),
            400: "Bad Request - Validation errors"
        },
        tags=['Authentication']
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully!",
                "user": {
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OTPRequestView(views.APIView):
    permission_classes = []  # Allow unauthenticated access
    
    @swagger_auto_schema(
        operation_description="Request OTP for phone verification",
        operation_summary="Request OTP",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number'],
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number in international format', example='+1234567890'),
            }
        ),
        responses={
            200: openapi.Response(
                description="OTP sent successfully",
                examples={
                    "application/json": {
                        "message": "OTP sent successfully!"
                    }
                }
            ),
            400: "Bad Request - Phone number required"
        },
        tags=['Authentication - OTP']
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')
        
        if not phone_number:
            return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        otp_code = str(random.randint(100000, 999999))  # Generate 6-digit OTP

        # Save OTP to the database
        otp_instance = PhoneOTP.objects.create(phone_number=phone_number, code=otp_code)

        # Send OTP via Twilio
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=f"Your verification code is {otp_code}",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone_number
            )
            return Response({"message": "OTP sent successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            # If Twilio fails, still return success for development
            return Response({
                "message": "OTP generated (Twilio error - check configuration)",
                "otp_code": otp_code,  # Only for development
                "error": str(e)
            }, status=status.HTTP_200_OK)


class OTPVerifyView(views.APIView):
    permission_classes = []  # Allow unauthenticated access
    
    @swagger_auto_schema(
        operation_description="Verify OTP code for phone verification",
        operation_summary="Verify OTP",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['phone_number', 'otp_code'],
            properties={
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number used to request OTP', example='+1234567890'),
                'otp_code': openapi.Schema(type=openapi.TYPE_STRING, description='6-digit OTP code', example='123456'),
            }
        ),
        responses={
            200: openapi.Response(
                description="OTP verified successfully",
                examples={
                    "application/json": {
                        "message": "OTP verified successfully!"
                    }
                }
            ),
            400: "Bad Request - Invalid or expired OTP"
        },
        tags=['Authentication - OTP']
    )
    def post(self, request):
        phone_number = request.data.get('phone_number')
        otp_code = request.data.get('otp_code')

        otp = PhoneOTP.objects.filter(phone_number=phone_number, code=otp_code).first()

        if not otp or otp.is_otp_expired():
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        
        otp.verified = True
        otp.save()

        return Response({"message": "OTP verified successfully!"}, status=status.HTTP_200_OK)



class UserLoginView(views.APIView):
    permission_classes = []  # Allow unauthenticated access
    
    @swagger_auto_schema(
        operation_description="Login with email and password to get JWT tokens",
        operation_summary="User Login",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='User email address', example='john.doe@example.com'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='User password', example='SecurePass123!'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Login successful",
                examples={
                    "application/json": {
                        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "user": {
                            "id": 1,
                            "username": "johndoe",
                            "full_name": "John Doe",
                            "email": "john.doe@example.com",
                            "phone_number": "+1234567890"
                        }
                    }
                }
            ),
            401: "Authentication Failed - Invalid credentials"
        },
        tags=['Authentication']
    )
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            raise AuthenticationFailed('Email and password are required')

        user = authenticate(request, username=email, password=password)

        if user is None:
            raise AuthenticationFailed('Invalid credentials')

        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token

        return Response({
            'refresh': str(refresh),
            'access': str(access_token),
            'user': {
                'id': user.id,
                'username': user.username,
                'full_name': user.full_name,
                'email': user.email,
                'phone_number': user.phone_number
            }
        }, status=status.HTTP_200_OK)


class UserLogoutView(views.APIView):
    """Logout user by blacklisting refresh token"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Logout user by blacklisting the refresh token",
        operation_summary="User Logout",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to blacklist', example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Logout successful",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Logout successful"
                    }
                }
            ),
            400: "Bad Request - Invalid token"
        },
        tags=['Authentication']
    )
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'error': 'Refresh token is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'success': True,
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid token or token already blacklisted',
                'details': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    



class PasswordResetView(views.APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            # Send the reset email
            serializer.save()
            return Response({"message": "Password reset link has been sent to your email."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(views.APIView):
    """Get authenticated user's profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get current authenticated user's profile information",
        operation_summary="Get User Profile",
        responses={
            200: openapi.Response(
                description="User profile retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "user": {
                            "id": 1,
                            "username": "johndoe",
                            "email": "john.doe@example.com",
                            "full_name": "John Doe",
                            "phone_number": "+1234567890",
                            "profile_picture": "/media/profiles/pic.jpg",
                            "profile_picture_url": "http://localhost:8000/media/profiles/pic.jpg",
                            "date_joined": "2024-01-15T10:30:00Z",
                            "last_login": "2024-01-20T14:25:00Z"
                        }
                    }
                }
            ),
            401: "Unauthorized - Authentication required"
        },
        tags=['User Profile']
    )
    def get(self, request):
        """Get user profile"""
        serializer = UserProfileSerializer(request.user, context={'request': request})
        return Response({
            'success': True,
            'user': serializer.data
        })


class UserProfileUpdateView(views.APIView):
    """Update authenticated user's profile"""
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    @swagger_auto_schema(
        operation_description="Update user profile (partial update). Supports multipart/form-data for image upload.",
        operation_summary="Update User Profile",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'full_name': openapi.Schema(type=openapi.TYPE_STRING, description='Full name', example='John Doe Updated'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number (international format)', example='+1987654321'),
                'profile_picture': openapi.Schema(type=openapi.TYPE_FILE, description='Profile picture (JPG, PNG, GIF, WEBP - max 5MB)'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Profile updated successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Profile updated successfully",
                        "user": {
                            "id": 1,
                            "username": "johndoe",
                            "email": "john.doe@example.com",
                            "full_name": "John Doe Updated",
                            "phone_number": "+1987654321",
                            "profile_picture_url": "http://localhost:8000/media/profiles/new_pic.jpg"
                        }
                    }
                }
            ),
            400: "Bad Request - Validation errors",
            401: "Unauthorized - Authentication required"
        },
        tags=['User Profile']
    )
    def patch(self, request):
        """Update user profile (supports multipart/form-data for image upload)"""
        serializer = UserProfileUpdateSerializer(
            request.user, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'user': UserProfileSerializer(user, context={'request': request}).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_description="Full update of user profile. Supports multipart/form-data for image upload.",
        operation_summary="Full Update User Profile",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['full_name', 'phone_number'],
            properties={
                'full_name': openapi.Schema(type=openapi.TYPE_STRING, description='Full name', example='John Doe Updated'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number (international format)', example='+1987654321'),
                'profile_picture': openapi.Schema(type=openapi.TYPE_FILE, description='Profile picture (JPG, PNG, GIF, WEBP - max 5MB)'),
            }
        ),
        responses={
            200: "Profile updated successfully",
            400: "Bad Request - Validation errors",
            401: "Unauthorized"
        },
        tags=['User Profile']
    )
    def put(self, request):
        """Full update of user profile (supports multipart/form-data for image upload)"""
        serializer = UserProfileUpdateSerializer(
            request.user, 
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully',
                'user': UserProfileSerializer(user, context={'request': request}).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(views.APIView):
    """Change password for authenticated user"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Change password for authenticated user",
        operation_summary="Change Password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['old_password', 'new_password', 'confirm_new_password'],
            properties={
                'old_password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='Current password', example='OldPassword123!'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='New password (min 8 characters)', example='NewPassword123!'),
                'confirm_new_password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='Confirm new password', example='NewPassword123!'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Password changed successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Password changed successfully. Please login again with your new password."
                    }
                }
            ),
            400: "Bad Request - Validation errors",
            401: "Unauthorized"
        },
        tags=['User Profile']
    )
    def post(self, request):
        """Change user password"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'success': True,
                'message': 'Password changed successfully. Please login again with your new password.'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(views.APIView):
    """Request password reset (forgot password)"""
    permission_classes = []  # Allow unauthenticated access
    
    @swagger_auto_schema(
        operation_description="Request password reset link via email",
        operation_summary="Forgot Password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Registered email address', example='john.doe@example.com'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Password reset email sent",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Password reset link has been sent to your email. Please check your inbox."
                    }
                }
            ),
            400: "Bad Request - Invalid email",
            500: "Internal Server Error - Email sending failed"
        },
        tags=['Password Reset']
    )
    def post(self, request):
        """Send password reset email"""
        serializer = ForgotPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({
                    'success': True,
                    'message': 'Password reset link has been sent to your email. Please check your inbox.'
                })
            except Exception as e:
                return Response({
                    'error': 'Failed to send email',
                    'details': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(views.APIView):
    """Reset password with token from email"""
    permission_classes = []  # Allow unauthenticated access
    
    def get(self, request, uid=None, token=None):
        """Show password reset form"""
        from django.shortcuts import render
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_decode
        
        # Get main domain for login link
        main_domain = os.getenv('MAIN_DOMAIN', 'https://h2o427-backend-u9bx.onrender.com')
        login_url = f"{main_domain}/api/auth/login/"
        
        context = {
            'uid': uid,
            'token': token,
            'login_url': login_url,
            'error': None,
            'success': None
        }
        
        # Verify token if provided in URL
        if uid and token:
            try:
                user_id = urlsafe_base64_decode(uid).decode()
                user = User.objects.get(pk=user_id)
                
                if not default_token_generator.check_token(user, token):
                    context['error'] = 'This password reset link is invalid or has expired. Please request a new one.'
                    
            except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                context['error'] = 'Invalid reset link. Please request a new password reset.'
        
        return render(request, 'authentication/reset_password.html', context)
    
    @swagger_auto_schema(
        operation_description="Reset password using token from email (API endpoint for programmatic access)",
        operation_summary="Reset Password (API)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['uid', 'token', 'new_password', 'confirm_new_password'],
            properties={
                'uid': openapi.Schema(type=openapi.TYPE_STRING, description='User ID from reset link', example='NDk'),
                'token': openapi.Schema(type=openapi.TYPE_STRING, description='Token from reset link', example='cy83ft-0ef9e8a23abb153c18b247d0bc4de37c'),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='New password (min 8 characters)', example='NewSecurePass123!'),
                'confirm_new_password': openapi.Schema(type=openapi.TYPE_STRING, format='password', description='Confirm new password', example='NewSecurePass123!'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Password reset successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Password reset successfully. You can now login with your new password."
                    }
                }
            ),
            400: "Bad Request - Invalid token or validation errors"
        },
        tags=['Password Reset']
    )
    def post(self, request, uid=None, token=None):
        """Reset password with token"""
        from django.shortcuts import render, redirect
        
        # Get main domain for login link
        main_domain = os.getenv('MAIN_DOMAIN', 'https://h2o427-backend-u9bx.onrender.com')
        login_url = f"{main_domain}/api/auth/login/"
        
        # Check if it's a form submission (from HTML page) or API request (JSON)
        is_form_submission = request.content_type == 'application/x-www-form-urlencoded' or \
                            request.content_type.startswith('multipart/form-data')
        
        # Prepare data from either URL params + form or JSON body
        if uid and token:
            # Form submission from HTML page
            data = {
                'uid': uid,
                'token': token,
                'new_password': request.POST.get('new_password') if is_form_submission else request.data.get('new_password'),
                'confirm_new_password': request.POST.get('confirm_new_password') if is_form_submission else request.data.get('confirm_new_password'),
            }
        else:
            # API request with all data in body
            data = request.data
        
        serializer = ResetPasswordSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()
            
            # If form submission, render success page
            if is_form_submission:
                context = {
                    'success': 'Password reset successfully! You can now login with your new password.',
                    'login_url': login_url,
                    'error': None
                }
                return render(request, 'authentication/reset_password.html', context)
            
            # If API request, return JSON
            return Response({
                'success': True,
                'message': 'Password reset successfully. You can now login with your new password.'
            })
        
        # Handle errors
        if is_form_submission:
            error_messages = []
            for field, errors in serializer.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            
            context = {
                'uid': uid or data.get('uid'),
                'token': token or data.get('token'),
                'login_url': login_url,
                'error': ' | '.join(error_messages),
                'success': None
            }
            return render(request, 'authentication/reset_password.html', context)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

