from rest_framework import serializers
from .models import Request, Report
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()

class RequestSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    days_since_created = serializers.SerializerMethodField()
    report_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Request
        fields = [
            'id', 'user', 'user_name', 'user_email', 'name', 'dob', 
            'city', 'state', 'email', 'phone_number', 'status', 
            'payment_status', 'report_type', 'payment_amount', 'payment_date',
            'stripe_checkout_session_id', 'stripe_payment_intent_id',
            'created_at', 'updated_at', 'days_since_created', 'report_price'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'days_since_created', 
                           'payment_status', 'payment_amount', 'payment_date',
                           'stripe_checkout_session_id', 'stripe_payment_intent_id', 'report_price']
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
    
    def get_report_price(self, obj):
        return obj.get_report_price()

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

class DetailedReportSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for detailed report view with all verification fields"""
    request_name = serializers.CharField(source='request.name', read_only=True)
    request_email = serializers.CharField(source='request.email', read_only=True)
    request_phone = serializers.CharField(source='request.phone_number', read_only=True)
    request_dob = serializers.DateField(source='request.dob', read_only=True)
    request_city = serializers.CharField(source='request.city', read_only=True)
    request_state = serializers.CharField(source='request.state', read_only=True)
    request_status = serializers.CharField(source='request.status', read_only=True)
    file_size = serializers.SerializerMethodField()
    
    class Meta:
        model = Report
        fields = [
            # Basic report info
            'id', 'generated_at', 'notes', 'pdf', 'file_size',
            # Request subject info
            'request_name', 'request_email', 'request_phone', 'request_dob',
            'request_city', 'request_state', 'request_status',
            # Identity Verification
            'ssn_validation', 'address_history', 'identity_cross_reference', 'database_match',
            # Criminal History
            'federal_criminal_records', 'state_criminal_records', 'county_criminal_records',
            'adult_offender_registry', 'state_searched', 'county_searched',
            # Address History
            'address_history_details',
            # Education Verification
            'education_verified', 'education_degree', 'education_institution',
            'education_graduation_year', 'education_status',
            # Employment Verification
            'employment_verified', 'employment_details',
            # Final Summary
            'final_summary', 'recommendation', 'verification_status'
        ]
        read_only_fields = fields

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


class AdminReportFormSerializer(serializers.ModelSerializer):
    """Admin serializer for creating/updating complete background check reports"""
    
    class Meta:
        model = Report
        fields = [
            'request', 'pdf', 'notes',
            # Identity Verification
            'ssn_validation', 'address_history', 'identity_cross_reference', 'database_match',
            # Criminal History
            'federal_criminal_records', 'state_criminal_records', 'county_criminal_records',
            'adult_offender_registry', 'state_searched', 'county_searched',
            # Address History
            'address_history_details',
            # Education Verification
            'education_verified', 'education_degree', 'education_institution',
            'education_graduation_year', 'education_status',
            # Employment Verification
            'employment_verified', 'employment_details',
            # Final Summary
            'final_summary', 'recommendation', 'verification_status'
        ]
        extra_kwargs = {
            'request': {'required': True},
            'pdf': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
        # If education is verified, require degree and institution
        if data.get('education_verified'):
            if not data.get('education_degree') or not data.get('education_institution'):
                raise serializers.ValidationError(
                    "Education degree and institution are required when education is verified"
                )
        return data

    def create(self, validated_data):
        # Get the request and update its status to Completed
        request_obj = validated_data.get('request')
        request_obj.status = 'Completed'
        request_obj.save()
        
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Update the request status if report is being updated
        if 'request' in validated_data:
            request_obj = validated_data.get('request')
            request_obj.status = 'Completed'
            request_obj.save()
        
        return super().update(instance, validated_data)


class PaymentPricingSerializer(serializers.Serializer):
    """Serializer for selecting plan and creating payment"""
    plan_id = serializers.IntegerField(
        help_text="ID of the subscription plan to purchase"
    )
    
    def validate_plan_id(self, value):
        from subscriptions.models import SubscriptionPlan
        
        try:
            plan = SubscriptionPlan.objects.get(id=value, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Invalid plan ID or plan is not active")
        
        return value
