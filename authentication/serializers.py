from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, 
        min_length=8,
        help_text="Password must be at least 8 characters long",
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        help_text="Re-enter the same password for verification",
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password_confirm']
        extra_kwargs = {
            'username': {
                'help_text': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'
            },
            'email': {
                'help_text': 'Enter a valid email address'
            },
            'first_name': {
                'help_text': 'Optional. Your first name'
            },
            'last_name': {
                'help_text': 'Optional. Your last name'
            }
        }

    def validate_password(self, value):
        """Validate password using Django's built-in validators"""
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Passwords don't match"
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=150,
        help_text="Enter your username",
        style={'placeholder': 'Username'}
    )
    password = serializers.CharField(
        write_only=True,
        help_text="Enter your password",
        style={'input_type': 'password', 'placeholder': 'Password'}
    )

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError(
                    'Invalid username or password',
                    code='authorization'
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled',
                    code='authorization'
                )
            attrs['user'] = user
        else:
            raise serializers.ValidationError(
                'Must include username and password',
                code='authorization'
            )
        return attrs

class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    total_requests = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'is_staff', 'date_joined', 'total_requests'
        ]
        read_only_fields = ['id', 'username', 'is_staff', 'date_joined', 'full_name', 'total_requests']
        extra_kwargs = {
            'email': {
                'help_text': 'Update your email address'
            },
            'first_name': {
                'help_text': 'Update your first name'
            },
            'last_name': {
                'help_text': 'Update your last name'
            }
        }

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def get_total_requests(self, obj):
        return obj.request_set.count() if hasattr(obj, 'request_set') else 0

class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users with minimal information"""
    full_name = serializers.SerializerMethodField()
    total_requests = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email', 'is_staff', 'date_joined', 'total_requests']
        read_only_fields = fields

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.username

    def get_total_requests(self, obj):
        return obj.request_set.count() if hasattr(obj, 'request_set') else 0
