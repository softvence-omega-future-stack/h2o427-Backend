import random
from rest_framework import status, views
from rest_framework.response import Response
from .serializers import UserRegistrationSerializer, PasswordResetSerializer
from .models import PhoneOTP, User
from twilio.rest import Client
from django.conf import settings


from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework.exceptions import AuthenticationFailed



class UserRegistrationView(views.APIView):
    permission_classes = []  # Allow unauthenticated access
    
    def get(self, request):
        """Display registration form in browsable API"""
        serializer = UserRegistrationSerializer()
        return Response({
            "message": "User Registration Endpoint",
            "fields": serializer.data if hasattr(serializer, 'data') else {
                "username": "string (optional, will use email if not provided)",
                "full_name": "string",
                "email": "string (required, unique)",
                "phone_number": "string (optional)",
                "password": "string (required)",
                "confirm_password": "string (required)"
            }
        })
    
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
    
    def get(self, request):
        """Display OTP request form"""
        return Response({
            "message": "Request OTP for phone verification",
            "fields": {
                "phone_number": "string (required, international format)"
            }
        })
    
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
    
    def get(self, request):
        """Display OTP verification form"""
        return Response({
            "message": "Verify OTP",
            "fields": {
                "phone_number": "string (required)",
                "otp_code": "string (required, 6 digits)"
            }
        })
    
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
    
    def get(self, request):
        """Display login form in browsable API"""
        return Response({
            "message": "User Login Endpoint",
            "fields": {
                "email": "string (required, can also use username)",
                "password": "string (required)"
            }
        })
    
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
    



class PasswordResetView(views.APIView):
    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            # Send the reset email
            serializer.save()
            return Response({"message": "Password reset link has been sent to your email."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

