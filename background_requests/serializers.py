from rest_framework import serializers
from .models import Request, Report
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()

class RequestSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    days_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = Request
        fields = [
            'id', 'user', 'user_name', 'user_email', 'name', 'dob', 
            'city', 'state', 'email', 'phone_number', 'status', 
            'created_at', 'updated_at', 'days_since_created'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'days_since_created']
        extra_kwargs = {
            'name': {
                'help_text': 'Full name of the person for background check'
            },
            'dob': {
                'help_text': 'Date of birth (YYYY-MM-DD format)'
            },
            'city': {
                'help_text': 'City of residence'
            },
            'state': {
                'help_text': 'State/Province (e.g., NY, CA, TX)'
            },
            'email': {
                'help_text': 'Contact email address'
            },
            'phone_number': {
                'help_text': 'Contact phone number (e.g., +1234567890)'
            }
        }

    def get_days_since_created(self, obj):
        return (date.today() - obj.created_at.date()).days

class RequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Request
        fields = ['name', 'dob', 'city', 'state', 'email', 'phone_number']
        extra_kwargs = {
            'name': {
                'help_text': 'Full name of the person for background check',
                'style': {'placeholder': 'John Doe'}
            },
            'dob': {
                'help_text': 'Date of birth (YYYY-MM-DD format)',
                'style': {'input_type': 'date'}
            },
            'city': {
                'help_text': 'City of residence',
                'style': {'placeholder': 'New York'}
            },
            'state': {
                'help_text': 'State/Province (e.g., NY, CA, TX)',
                'style': {'placeholder': 'NY'}
            },
            'email': {
                'help_text': 'Contact email address',
                'style': {'input_type': 'email', 'placeholder': 'john.doe@example.com'}
            },
            'phone_number': {
                'help_text': 'Contact phone number',
                'style': {'placeholder': '+1234567890'}
            }
        }

    def validate_dob(self, value):
        """Validate date of birth"""
        if value > date.today():
            raise serializers.ValidationError("Date of birth cannot be in the future")
        
        age = (date.today() - value).days / 365.25
        if age < 18:
            raise serializers.ValidationError("Person must be at least 18 years old")
        if age > 120:
            raise serializers.ValidationError("Please enter a valid date of birth")
        
        return value

    def validate_state(self, value):
        """Validate state format"""
        if len(value) > 10:
            raise serializers.ValidationError("State should be abbreviated (e.g., NY, CA)")
        return value.upper()

class RequestListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing requests"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    days_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = Request
        fields = ['id', 'name', 'user_name', 'status', 'created_at', 'days_since_created']
        read_only_fields = fields

    def get_days_since_created(self, obj):
        return (date.today() - obj.created_at.date()).days

class RequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating request status (admin only)"""
    class Meta:
        model = Request
        fields = ['status']
        extra_kwargs = {
            'status': {
                'help_text': 'Update the status of this background check request'
            }
        }

class ReportSerializer(serializers.ModelSerializer):
    request_name = serializers.CharField(source='request.name', read_only=True)
    request_status = serializers.CharField(source='request.status', read_only=True)
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = ['id', 'request', 'request_name', 'request_status', 'pdf', 'generated_at', 'notes', 'file_size']
        read_only_fields = ['generated_at', 'file_size']
        extra_kwargs = {
            'request': {
                'help_text': 'Select the background check request for this report'
            },
            'pdf': {
                'help_text': 'Upload the PDF report file'
            },
            'notes': {
                'help_text': 'Optional notes about the background check findings'
            }
        }

    def get_file_size(self, obj):
        if obj.pdf and hasattr(obj.pdf, 'size'):
            size = obj.pdf.size
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "No file"

class ReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating reports"""
    class Meta:
        model = Report
        fields = ['request', 'pdf', 'notes']
        extra_kwargs = {
            'request': {
                'help_text': 'Select the background check request',
                'queryset': Request.objects.filter(status__in=['Pending', 'In Progress'])
            },
            'pdf': {
                'help_text': 'Upload the background check report (PDF format)',
                'required': True
            },
            'notes': {
                'help_text': 'Optional notes about the findings',
                'required': False,
                'allow_blank': True
            }
        }

