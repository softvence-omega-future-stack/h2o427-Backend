from rest_framework import serializers
from .models import User
from django.contrib.auth.hashers import make_password, check_password
import os


from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings

class UserRegistrationSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone_number', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        # Remove confirm_password from validated_data as it's not a model field
        validated_data.pop('confirm_password', None)
        
        # Create user with hashed password
        user = User.objects.create_user(
            username=validated_data.get('username', validated_data['email']),
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
            phone_number=validated_data.get('phone_number', '')
        )
        return user


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            # Check if the user exists
            user = get_user_model().objects.get(email=value)
        except get_user_model().DoesNotExist:
            raise serializers.ValidationError("No user found with this email.")
        return value

    def save(self):
        email = self.validated_data['email']
        user = get_user_model().objects.get(email=email)

        # Generate a password reset token and UID
        uid = urlsafe_base64_encode(user.pk.encode())
        token = default_token_generator.make_token(user)

        # Prepare the password reset URL
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

        # Send email with password reset link
        send_mail(
            subject="Password Reset Request",
            message=f"Click the link below to reset your password:\n{reset_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for viewing user profile"""
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name', 'phone_number', 'profile_picture', 'profile_picture_url', 'date_joined', 'last_login']
        read_only_fields = ['id', 'username', 'email', 'date_joined', 'last_login', 'profile_picture_url']
    
    def get_profile_picture_url(self, obj):
        """Get full URL for profile picture"""
        if obj.profile_picture:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile_picture.url)
            return obj.profile_picture.url
        return None


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = ['full_name', 'phone_number', 'profile_picture']
        extra_kwargs = {
            'full_name': {
                'required': False,
                'help_text': 'Your full name'
            },
            'phone_number': {
                'required': False,
                'help_text': 'Your phone number (international format, e.g., +1234567890)'
            },
            'profile_picture': {
                'required': False,
                'help_text': 'Upload profile picture (JPG, PNG, max 5MB)'
            }
        }
    
    def validate_phone_number(self, value):
        """Validate phone number format"""
        if value and not value.startswith('+'):
            raise serializers.ValidationError("Phone number must be in international format (start with +)")
        return value
    
    def validate_profile_picture(self, value):
        """Validate profile picture"""
        if value:
            # Check file size (max 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image file size must be less than 5MB")
            
            # Check file type
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(value, 'content_type') and value.content_type not in allowed_types:
                raise serializers.ValidationError("Only JPG, PNG, GIF, and WEBP images are allowed")
        
        return value
    
    def update(self, instance, validated_data):
        """Update user profile"""
        # Delete old profile picture if new one is uploaded
        if 'profile_picture' in validated_data and validated_data['profile_picture']:
            if instance.profile_picture:
                # Delete old file
                instance.profile_picture.delete(save=False)
        
        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data['profile_picture']
        
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        """Validate that old password is correct"""
        user = self.context['request'].user
        if not check_password(value, user.password):
            raise serializers.ValidationError("Old password is incorrect")
        return value
    
    def validate(self, data):
        """Validate that new passwords match"""
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords do not match"})
        
        # Validate password strength
        if len(data['new_password']) < 8:
            raise serializers.ValidationError({"new_password": "Password must be at least 8 characters long"})
        
        return data
    
    def save(self):
        """Change the user's password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    """Serializer for forgot password (request reset)"""
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Check if user with this email exists"""
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address")
        return value
    
    def save(self):
        """Send password reset email"""
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        
        # Generate reset token
        uid = urlsafe_base64_encode(str(user.pk).encode())
        token = default_token_generator.make_token(user)
        
        # Use main domain for both links (https://h2o427-backend-u9bx.onrender.com)
        main_domain = os.getenv('MAIN_DOMAIN', 'https://h2o427-backend-u9bx.onrender.com')
        
        # Frontend reset page URL
        frontend_url = f"{main_domain}/reset-password/{uid}/{token}/"
        
        # API endpoint URL
        backend_url = f"{main_domain}/api/auth/reset-password/"
        
        # Send email
        try:
            send_mail(
                subject="Password Reset Request - Background Check System",
                message=f"""
Hello {user.full_name or user.username},

You requested to reset your password for your Background Check System account.

Click the link below to reset your password:
{frontend_url}

Or use this API endpoint directly:
{backend_url}

This link will expire in 24 hours.

If you didn't request this, please ignore this email.

Best regards,
Background Check System Team
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            raise serializers.ValidationError(f"Failed to send email: {str(e)}")


class ResetPasswordSerializer(serializers.Serializer):
    """Serializer for resetting password with token"""
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        """Validate token and passwords"""
        # Validate passwords match
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match"})
        
        # Validate password strength
        if len(data['new_password']) < 8:
            raise serializers.ValidationError({"new_password": "Password must be at least 8 characters long"})
        
        # Decode UID
        try:
            uid = urlsafe_base64_decode(data['uid']).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid reset link"})
        
        # Validate token
        if not default_token_generator.check_token(user, data['token']):
            raise serializers.ValidationError({"token": "Invalid or expired reset link"})
        
        # Store user in validated data for save method
        data['user'] = user
        return data
    
    def save(self):
        """Reset the password"""
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
