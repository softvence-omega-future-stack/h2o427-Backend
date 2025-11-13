from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from .models import Request, Report
from .serializers import (
    RequestSerializer, RequestCreateSerializer, RequestListSerializer, 
    RequestUpdateSerializer, ReportSerializer, ReportCreateSerializer
)
from subscriptions.models import UserSubscription

class RequestViewSet(viewsets.ModelViewSet):
    """
    Background Check Request Management
    
    Provides CRUD operations for background check requests.
    Clients can only access their own requests, admins can see all.
    """
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'state', 'created_at']
    search_fields = ['name', 'email', 'city', 'user__username']
    ordering_fields = ['created_at', 'updated_at', 'name', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        # Handle Swagger schema generation
        if getattr(self, 'swagger_fake_view', False):
            return Request.objects.none()
            
        if self.request.user.is_staff:
            # Admin can see all requests
            return Request.objects.all().order_by('-created_at')
        else:
            # Clients can only see their own requests
            return Request.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return RequestCreateSerializer
        elif self.action == 'list':
            return RequestListSerializer
        elif self.action == 'partial_update' and self.request.user.is_staff:
            return RequestUpdateSerializer
        return RequestSerializer

    @swagger_auto_schema(
        operation_description="Submit a new background check request. No subscription required - payment is made after submission.",
        operation_summary="Submit New Background Check Request",
        operation_id="request_create",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'dob', 'city', 'state', 'email', 'phone_number'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Full name of the person', example='John Smith'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, format='email', description='Email address', example='john.smith@example.com'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone number', example='+1234567890'),
                'dob': openapi.Schema(type=openapi.TYPE_STRING, format='date', description='Date of birth (YYYY-MM-DD)', example='1990-05-15'),
                'city': openapi.Schema(type=openapi.TYPE_STRING, description='City', example='New York'),
                'state': openapi.Schema(type=openapi.TYPE_STRING, description='State (2-letter code)', example='NY'),
            }
        ),
        responses={
            201: openapi.Response(
                description="Request created successfully - proceed to payment",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Background check request submitted successfully",
                        "request": {
                            "id": 1,
                            "name": "John Smith",
                            "email": "john.smith@example.com",
                            "phone_number": "+1234567890",
                            "dob": "1990-05-15",
                            "city": "New York",
                            "state": "NY",
                            "status": "Pending",
                            "payment_status": "payment_pending",
                            "created_at": "2024-01-20T10:30:00Z"
                        },
                        "next_step": {
                            "action": "select_payment",
                            "url": "/api/requests/api/{request_id}/select-pricing/",
                            "message": "Please select your report type and proceed to payment"
                        }
                    }
                }
            ),
            400: "Bad Request - Validation errors"
        },
        tags=['Background Check Requests']
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        request_obj = serializer.instance
        
        return Response({
            'success': True,
            'message': 'Background check request submitted successfully',
            'request': RequestSerializer(request_obj).data,
            'next_step': {
                'action': 'select_payment',
                'url': f'/api/requests/api/{request_obj.id}/select-pricing/',
                'message': 'Please select your report type ($25 or $50) and proceed to payment',
                'pricing_options': {
                    'basic': {'price': 25, 'features': 'Identity verification, criminal history check'},
                    'premium': {'price': 50, 'features': 'All basic features + employment & education verification'}
                }
            }
        }, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        # Simply create the request - no subscription checks
        serializer.save(user=self.request.user, payment_status='payment_pending')

    def perform_update(self, serializer):
        # Only admins can update status
        if not self.request.user.is_staff:
            # Clients can only update their contact info, not status
            serializer.validated_data.pop('status', None)
        serializer.save()

    @swagger_auto_schema(
        operation_summary="Download Background Check Report",
        operation_description="Download the PDF report for a completed background check request.",
        operation_id="request_download_report",
        tags=['Background Check Reports'],
        responses={
            200: openapi.Response(
                description="Report download information",
                examples={
                    "application/json": {
                        "success": True,
                        "report": {
                            "id": 1,
                            "download_url": "http://localhost:8000/media/reports/report_1.pdf",
                            "filename": "report_1.pdf",
                            "generated_at": "2024-01-22T14:20:00Z",
                            "file_size_mb": "1.50 MB"
                        }
                    }
                }
            ),
            404: "Report not found or not available yet"
        }
    )
    @action(detail=True, methods=['get'], url_path='download-report', url_name='download-report')
    def download_report(self, request, pk=None):
        """Allow clients to download their background check report"""
        try:
            bg_request = self.get_object()
            
            # Check if report exists
            if not hasattr(bg_request, 'report'):
                return Response(
                    {
                        'error': 'Report not available yet',
                        'status': bg_request.status,
                        'message': 'The background check is still being processed. Please check back later.'
                    }, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            report = bg_request.report
            
            # Check if PDF file exists
            if not report.pdf:
                return Response(
                    {
                        'error': 'Report PDF not available',
                        'message': 'The report exists but the PDF file is missing.'
                    }, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if file physically exists
            try:
                file_size = report.pdf.size
                filename = report.pdf.name.split('/')[-1]
            except (FileNotFoundError, OSError):
                return Response({
                    'error': 'PDF file not found',
                    'message': 'The PDF file is missing from the server. Please contact support.',
                    'request_id': bg_request.id,
                    'report_id': report.id
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Return report details with download URL
            return Response({
                'success': True,
                'report': {
                    'id': report.id,
                    'download_url': request.build_absolute_uri(report.pdf.url),
                    'filename': filename,
                    'generated_at': report.generated_at,
                    'notes': report.notes,
                    'file_size': file_size,
                    'file_size_mb': f"{file_size / (1024 * 1024):.2f} MB"
                },
                'request': {
                    'id': bg_request.id,
                    'name': bg_request.name,
                    'status': bg_request.status
                }
            })
            
        except Request.DoesNotExist:
            return Response(
                {'error': 'Request not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'error': 'An error occurred',
                    'details': str(e)
                }, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="View detailed report information for a completed background check",
        operation_summary="View Report Details",
        responses={
            200: openapi.Response(
                description="Report details retrieved successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "background_check": {
                            "id": 1,
                            "name": "John Doe",
                            "email": "john@example.com",
                            "phone_number": "+1234567890",
                            "dob": "1990-01-15",
                            "city": "New York",
                            "state": "NY",
                            "status": "Completed",
                            "submitted_date": "2024-01-20T10:30:00Z",
                            "completed_date": "2024-01-22T14:20:00Z"
                        },
                        "report": {
                            "id": 1,
                            "generated_at": "2024-01-22T14:20:00Z",
                            "notes": "Background check completed successfully. No issues found.",
                            "findings": {
                                "criminal_records": "No criminal records found",
                                "verification_status": "Verified"
                            }
                        },
                        "download": {
                            "pdf_url": "http://localhost:8000/media/reports/report_1.pdf",
                            "filename": "report_1.pdf",
                            "file_size": "1.5 MB",
                            "expires_in": "7 days"
                        }
                    }
                }
            ),
            404: "Report not found or not completed yet",
            403: "Not authorized to view this report"
        },
        tags=['Background Check Reports']
    )
    @action(detail=True, methods=['get'], url_path='view-report', url_name='view-report')
    def view_report(self, request, pk=None):
        """View detailed report information for a completed background check"""
        try:
            bg_request = self.get_object()
            
            # Check if request belongs to user (unless admin)
            if not request.user.is_staff and bg_request.user != request.user:
                return Response(
                    {
                        'error': 'Permission denied',
                        'message': 'You can only view your own background check reports.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if background check is completed
            if bg_request.status != 'Completed':
                return Response(
                    {
                        'error': 'Report not available',
                        'message': f'Background check is currently "{bg_request.status}". Report will be available once completed.',
                        'current_status': bg_request.status,
                        'request_id': bg_request.id
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Check if report exists
            if not hasattr(bg_request, 'report'):
                return Response(
                    {
                        'error': 'Report not found',
                        'message': 'Background check is marked as completed but report has not been generated yet.',
                        'status': bg_request.status
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            report = bg_request.report
            
            # Check if PDF exists
            has_pdf = False
            pdf_url = None
            filename = None
            file_size = None
            
            try:
                if report.pdf and report.pdf.name:
                    has_pdf = True
                    pdf_url = request.build_absolute_uri(report.pdf.url)
                    filename = report.pdf.name.split('/')[-1]
                    if report.pdf.size:
                        if report.pdf.size < 1024:
                            file_size = f"{report.pdf.size} bytes"
                        elif report.pdf.size < 1024 * 1024:
                            file_size = f"{report.pdf.size / 1024:.1f} KB"
                        else:
                            file_size = f"{report.pdf.size / (1024 * 1024):.2f} MB"
            except Exception:
                pass
            
            # Build comprehensive response
            response_data = {
                'success': True,
                'report_header': {
                    'title': 'Comprehensive Background Check Report',
                    'report_id': report.id,
                    'generated_at': report.generated_at.isoformat() if report.generated_at else None,
                    'verification_status': report.verification_status,
                    'status_label': 'Verification Complete' if report.verification_status == 'clear' else report.verification_status.replace('_', ' ').title()
                },
                'subject_information': {
                    'full_name': bg_request.name,
                    'date_of_birth': str(bg_request.dob) if bg_request.dob else None,
                    'email': bg_request.email,
                    'phone': bg_request.phone_number,
                    'location': f"{bg_request.city}, {bg_request.state}" if bg_request.city and bg_request.state else None,
                    'city': bg_request.city,
                    'state': bg_request.state
                },
                'verification_complete': {
                    'status': 'complete',
                    'message': 'All background checks have been processed and reviewed'
                },
                'identity_verification': {
                    'section_title': 'Identity Verification',
                    'status': 'verified',
                    'checks': {
                        'ssn_validation': {
                            'label': 'Social Security Number Validation',
                            'status': report.ssn_validation,
                            'icon': 'verified'
                        },
                        'address_history': {
                            'label': 'Address History',
                            'status': report.address_history,
                            'icon': 'verified'
                        },
                        'identity_cross_reference': {
                            'label': 'Identity Cross-Reference',
                            'status': report.identity_cross_reference,
                            'icon': 'clear'
                        },
                        'database_match': {
                            'label': 'Database Match',
                            'status': report.database_match,
                            'icon': 'verified'
                        }
                    }
                },
                'address_history_check': {
                    'section_title': 'Address History Check',
                    'status': 'clear',
                    'checks': {
                        'ssn_validation': {
                            'label': 'Social Security Number Validation',
                            'status': report.ssn_validation
                        },
                        'address_history': {
                            'label': 'Address History',
                            'status': report.address_history
                        },
                        'identity_cross_reference': {
                            'label': 'Identity Cross-Reference',
                            'status': report.identity_cross_reference
                        },
                        'database_match': {
                            'label': 'Database Match',
                            'status': report.database_match
                        }
                    },
                    'details': report.address_history_details or 'All address history has been verified and confirmed.'
                },
                'criminal_history_check': {
                    'section_title': 'Criminal History Check',
                    'status': 'clear',
                    'checks': {
                        'federal_criminal_records': {
                            'label': 'Federal Criminal Records Search',
                            'status': report.federal_criminal_records,
                            'details': report.federal_criminal_records
                        },
                        'state_criminal_records': {
                            'label': 'State Criminal Records Search',
                            'status': report.state_criminal_records,
                            'searched': report.state_searched or bg_request.state,
                            'details': f"Searched: {report.state_searched or bg_request.state} - {report.state_criminal_records}"
                        },
                        'county_criminal_records': {
                            'label': 'County Criminal Records Search',
                            'status': report.county_criminal_records,
                            'searched': report.county_searched or f"{bg_request.city} County",
                            'details': f"Searched: {report.county_searched or bg_request.city + ' County'} - {report.county_criminal_records}"
                        },
                        'sex_offender_registry': {
                            'label': 'National Sex Offender Registry',
                            'status': report.adult_offender_registry,
                            'details': report.adult_offender_registry
                        }
                    }
                },
                'education_verification': {
                    'section_title': 'Education Verification',
                    'status': 'verified' if report.education_verified else 'not_verified',
                    'verified': report.education_verified,
                    'details': {
                        'degree': report.education_degree or 'Not provided',
                        'institution': report.education_institution or 'Not provided',
                        'graduation_year': report.education_graduation_year or 'Not provided',
                        'status': report.education_status or 'Not verified'
                    } if report.education_verified else None
                },
                'employment_verification': {
                    'section_title': 'Employment Verification',
                    'status': 'verified' if report.employment_verified else 'not_applicable',
                    'verified': report.employment_verified,
                    'details': report.employment_details if report.employment_verified else 'Employment verification not requested or not applicable'
                },
                'final_summary': {
                    'section_title': 'Final Summary & Recommendation',
                    'summary_points': [
                        'Has successfully passed all required checks with no adverse findings.',
                        'No criminal records found at federal, state, or county levels',
                        'Credit standing is good with no negative marks' if report.verification_status == 'clear' else 'Review completed',
                        'Professional references provided positive feedback' if report.verification_status == 'clear' else 'Additional review may be needed'
                    ],
                    'detailed_summary': report.final_summary,
                    'recommendation': report.recommendation or 'Candidate has cleared all background checks and is approved for consideration.',
                    'overall_status': report.verification_status
                },
                'download': {
                    'available': has_pdf,
                    'pdf_url': pdf_url,
                    'filename': filename,
                    'file_size': file_size or 'Unknown',
                    'download_endpoint': f"/api/requests/{bg_request.id}/download-report/",
                    'note': 'Download the complete PDF report for detailed records'
                },
                'metadata': {
                    'request_id': bg_request.id,
                    'request_status': bg_request.status,
                    'submitted_date': bg_request.created_at.isoformat() if bg_request.created_at else None,
                    'completed_date': bg_request.updated_at.isoformat() if bg_request.updated_at else None,
                    'requestor': {
                        'id': bg_request.user.id,
                        'username': bg_request.user.username,
                        'email': bg_request.user.email
                    }
                },
                'admin_notes': report.notes or 'No additional notes from administrator'
            }
            
            return Response(response_data)
            
        except Request.DoesNotExist:
            return Response(
                {
                    'error': 'Background check request not found',
                    'message': 'The requested background check does not exist.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {
                    'error': 'An error occurred',
                    'message': 'Failed to retrieve report details.',
                    'details': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        method='get',
        operation_summary="Get Request Status Options (Admin)",
        operation_description="Get current status and available status options for a request. Admin only.",
        operation_id="request_admin_get_status",
        tags=['Admin - Request Management'],
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_PATH, description="Request ID", type=openapi.TYPE_INTEGER)
        ],
        responses={
            200: openapi.Response(
                description="Status information",
                examples={
                    "application/json": {
                        "request_id": 1,
                        "current_status": "Pending",
                        "available_statuses": ["Pending", "In Progress", "Completed"]
                    }
                }
            ),
            403: "Admin access required",
            404: "Request not found"
        }
    )
    @swagger_auto_schema(
        method='patch',
        operation_summary="Update Request Status (Admin)",
        operation_description="Update the status of a background check request. Admin only.",
        operation_id="request_admin_update_status",
        tags=['Admin - Request Management'],
        manual_parameters=[
            openapi.Parameter('id', openapi.IN_PATH, description="Request ID", type=openapi.TYPE_INTEGER)
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'status': openapi.Schema(type=openapi.TYPE_STRING, enum=['Pending', 'In Progress', 'Completed'], description='New status')
            }
        ),
        responses={
            200: "Status updated successfully",
            400: "Invalid status",
            403: "Admin access required",
            404: "Request not found"
        }
    )
    @action(detail=True, methods=['get', 'patch'], permission_classes=[permissions.IsAdminUser], url_path='update-status', url_name='update-status')
    def update_status(self, request, pk=None):
        """Update request status (admin only)"""
        bg_request = self.get_object()
        
        if request.method == 'GET':
            # Return current status and available options
            return Response({
                'request_id': bg_request.id,
                'request_name': bg_request.name,
                'current_status': bg_request.status,
                'available_statuses': ['Pending', 'In Progress', 'Completed'],
                'instructions': 'Send a PATCH request with {"status": "new_status"} to update',
                'example': {
                    'method': 'PATCH',
                    'body': {'status': 'Completed'}
                }
            })
        
        # PATCH request - update status
        serializer = RequestUpdateSerializer(bg_request, data=request.data, partial=True)
        if serializer.is_valid():
            old_status = bg_request.status
            serializer.save()
            return Response({
                'success': True,
                'message': f'Status updated from "{old_status}" to "{serializer.validated_data["status"]}"',
                'request': RequestSerializer(bg_request).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="Get Dashboard Statistics (Admin)",
        operation_description="Get admin dashboard statistics including request counts by status.",
        operation_id="request_admin_dashboard_stats",
        tags=['Admin - Dashboard'],
        responses={
            200: openapi.Response(
                description="Dashboard statistics",
                examples={
                    "application/json": {
                        "total_requests": 150,
                        "pending": 20,
                        "in_progress": 30,
                        "completed": 100,
                        "completion_rate": "66.7%"
                    }
                }
            ),
            403: "Admin access required"
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def dashboard_stats(self, request):
        """Get dashboard statistics (admin only)"""
        queryset = self.get_queryset()
        total = queryset.count()
        pending = queryset.filter(status='Pending').count()
        in_progress = queryset.filter(status='In Progress').count()
        completed = queryset.filter(status='Completed').count()
        
        return Response({
            'total_requests': total,
            'pending': pending,
            'in_progress': in_progress,
            'completed': completed,
            'completion_rate': f"{(completed/total*100):.1f}%" if total > 0 else "0%"
        })

    @swagger_auto_schema(
        operation_description="Get user's background check requests dashboard with status tracking and subscription details.",
        operation_summary="Get My Background Check Dashboard",
        operation_id="request_user_dashboard",
        tags=['Background Check Requests'],
        responses={
            200: openapi.Response(
                description="User dashboard with all requests",
                examples={
                    "application/json": {
                        "user": {
                            "id": 1,
                            "name": "John Doe",
                            "email": "john@example.com"
                        },
                        "subscription": {
                            "plan_name": "Premium Plan",
                            "requests_used": 5,
                            "requests_limit": 50,
                            "requests_remaining": 45,
                            "status": "active"
                        },
                        "requests_summary": {
                            "total": 5,
                            "pending": 1,
                            "in_progress": 2,
                            "completed": 2
                        },
                        "requests": [
                            {
                                "id": 1,
                                "name": "Jane Smith",
                                "email": "jane@example.com",
                                "status": "Completed",
                                "created_at": "2024-01-20T10:30:00Z",
                                "updated_at": "2024-01-22T14:20:00Z",
                                "has_report": True,
                                "report_download_url": "/api/requests/1/download-report/"
                            }
                        ]
                    }
                }
            ),
            401: "Unauthorized - Authentication required"
        }
    )
    @action(detail=False, methods=['get'], url_path='my-dashboard', url_name='my-dashboard')
    def my_dashboard(self, request):
        """Get user's dashboard with all their requests and subscription info"""
        user = request.user
        
        # Get user's requests
        user_requests = Request.objects.filter(user=user).order_by('-created_at')
        
        # Get subscription info
        subscription_data = None
        try:
            subscription = UserSubscription.objects.get(user=user)
            subscription_data = {
                'plan_name': subscription.plan.name if subscription.plan else None,
                'plan_price_per_report': str(subscription.plan.price_per_report) if subscription.plan else None,
                'free_trial_used': subscription.free_trial_used,
                'free_trial_available': subscription.can_use_free_trial,
                'reports_purchased': subscription.total_reports_purchased,
                'reports_used': subscription.total_reports_used,
                'reports_available': subscription.available_reports,
                'can_make_request': subscription.can_make_request,
                'created_at': subscription.created_at.isoformat() if subscription.created_at else None
            }
        except UserSubscription.DoesNotExist:
            subscription_data = {
                'plan_name': None,
                'message': 'No subscription found. Please select a plan.',
                'plans_url': '/api/subscriptions/plans/'
            }
        
        # Summary statistics
        requests_summary = {
            'total': user_requests.count(),
            'pending': user_requests.filter(status='Pending').count(),
            'in_progress': user_requests.filter(status='In Progress').count(),
            'completed': user_requests.filter(status='Completed').count()
        }
        
        # Serialize requests with report info
        requests_data = []
        for req in user_requests:
            # Check if report exists and has a PDF file (without reading the file content)
            has_report = False
            try:
                if hasattr(req, 'report') and req.report.pdf and req.report.pdf.name:
                    has_report = True
            except Exception:
                has_report = False
            
            request_data = {
                'id': req.id,
                'name': req.name,
                'email': req.email,
                'phone_number': req.phone_number,
                'dob': str(req.dob) if req.dob else None,  # Convert date to string
                'city': req.city,
                'state': req.state,
                'status': req.status,
                'created_at': req.created_at,
                'updated_at': req.updated_at,
                'has_report': has_report,
                'report_download_url': f"/api/requests/{req.id}/download-report/" if has_report else None,
            }
            requests_data.append(request_data)
        
        return Response({
            'user': {
                'id': user.id,
                'username': user.username,
                'name': user.full_name or user.username,
                'email': user.email,
                'phone_number': user.phone_number
            },
            'subscription': subscription_data,
            'requests_summary': requests_summary,
            'requests': requests_data,
            'message': 'Dashboard data retrieved successfully'
        })

    @swagger_auto_schema(
        operation_summary="Select Report Pricing",
        operation_description="Select report type ($25 Basic or $50 Premium) and create Stripe checkout session for payment.",
        operation_id="request_select_pricing",
        tags=['Background Check Payments'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['report_type'],
            properties={
                'report_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['basic', 'premium'],
                    description='Type of report: basic ($25) or premium ($50)'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Checkout session created - redirect to checkout_url",
                examples={
                    "application/json": {
                        "success": True,
                        "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_xxx",
                        "session_id": "cs_test_xxx",
                        "report_type": "basic",
                        "amount": 25.00,
                        "message": "Redirect user to checkout_url to complete payment"
                    }
                }
            ),
            400: "Invalid report type or request already paid",
            404: "Request not found"
        }
    )
    @action(detail=True, methods=['post'], url_path='select-pricing', url_name='select-pricing')
    def select_pricing(self, request, pk=None):
        """Select report pricing and create Stripe checkout session"""
        import stripe
        from django.conf import settings
        
        # Debug logging
        print(f"[DEBUG] Received data: {request.data}")
        print(f"[DEBUG] Request method: {request.method}")
        print(f"[DEBUG] Request user: {request.user}")
        print(f"[DEBUG] Request ID (pk): {pk}")
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        try:
            bg_request = self.get_object()
            
            # Check if request belongs to user
            if bg_request.user != request.user:
                return Response(
                    {'error': 'You can only pay for your own requests'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if already paid
            if bg_request.payment_status == 'payment_completed':
                return Response(
                    {'error': 'This request has already been paid for'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate plan ID
            from .serializers import PaymentPricingSerializer
            from subscriptions.models import SubscriptionPlan
            
            serializer = PaymentPricingSerializer(data=request.data)
            
            if not serializer.is_valid():
                return Response(
                    {
                        'error': 'Invalid data provided',
                        'details': serializer.errors,
                        'hint': 'Make sure to send {"plan_id": 1} with a valid plan ID'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            plan_id = serializer.validated_data['plan_id']
            
            # Get plan from database
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return Response(
                    {'error': 'Plan not found or not active'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get amount and description from plan
            amount = float(plan.price_per_report)
            description = plan.name
            report_type = plan.plan_type
            
            # Get frontend URL from settings or use default
            # For MTV pattern with Django templates, use the Django view URL
            frontend_url = request.build_absolute_uri('/api/requests')
            
            # Create Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(amount * 100),  # Convert to cents
                        'product_data': {
                            'name': description,
                            'description': f"Background check for {bg_request.name}",
                        },
                    },
                    'quantity': 1,
                }],
                mode='payment',
                # MTV pattern: redirect to Django template view
                success_url=f"{frontend_url}/payment-success/?request_id={bg_request.id}&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{frontend_url}/payment-cancelled/?request_id={bg_request.id}",
                metadata={
                    'request_id': bg_request.id,
                    'report_type': report_type,
                    'plan_id': plan.id,
                    'user_id': request.user.id
                }
            )
            
            # Update request with report type and session ID
            bg_request.report_type = report_type
            bg_request.payment_amount = amount
            bg_request.stripe_checkout_session_id = checkout_session.id
            bg_request.save()
            
            return Response({
                'success': True,
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id,
                'plan': {
                    'id': plan.id,
                    'name': plan.name,
                    'type': plan.plan_type
                },
                'amount': amount,
                'message': 'Redirect user to checkout_url to complete payment'
            })
            
        except Request.DoesNotExist:
            return Response(
                {'error': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error creating checkout session: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_summary="Confirm Payment",
        operation_description="Confirm payment from Stripe checkout and process the background check request.",
        operation_id="request_confirm_payment",
        tags=['Background Check Payments'],
        manual_parameters=[
            openapi.Parameter('session_id', openapi.IN_QUERY, description="Stripe Checkout Session ID", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: openapi.Response(
                description="Payment confirmed successfully",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Payment confirmed! Your background check is being processed.",
                        "request": {
                            "id": 1,
                            "status": "Pending",
                            "payment_status": "payment_completed",
                            "report_type": "basic",
                            "payment_amount": 25.00
                        }
                    }
                }
            ),
            400: "Payment not completed or invalid session",
            404: "Request not found"
        }
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny], url_path='confirm-payment', url_name='confirm-payment')
    def confirm_payment(self, request, pk=None):
        """Confirm payment after Stripe checkout"""
        import stripe
        from django.conf import settings
        from django.utils import timezone
        import traceback
        
        # Debug logging
        print(f"[DEBUG CONFIRM] Request ID: {pk}")
        print(f"[DEBUG CONFIRM] Session ID: {request.query_params.get('session_id')}")
        
        stripe.api_key = settings.STRIPE_SECRET_KEY
        
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'Checkout session ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            bg_request = self.get_object()
            print(f"[DEBUG CONFIRM] Found request: {bg_request.id}, payment_status: {bg_request.payment_status}")
            
            # Retrieve checkout session from Stripe
            print(f"[DEBUG CONFIRM] Retrieving Stripe session...")
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            print(f"[DEBUG CONFIRM] Payment status from Stripe: {checkout_session.payment_status}")
            
            # Check if payment was successful
            if checkout_session.payment_status != 'paid':
                return Response(
                    {'error': 'Payment not completed', 'status': checkout_session.payment_status},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update request with payment confirmation
            bg_request.payment_status = 'payment_completed'
            bg_request.stripe_payment_intent_id = checkout_session.payment_intent
            bg_request.payment_date = timezone.now()
            bg_request.save()
            
            print(f"[DEBUG CONFIRM] Payment confirmed successfully for request {bg_request.id}")
            
            return Response({
                'success': True,
                'message': 'Payment confirmed! Your background check is being processed.',
                'request': RequestSerializer(bg_request).data,
                'next_steps': {
                    'message': 'You will be notified when your report is ready',
                    'check_status_url': f'/api/requests/api/{bg_request.id}/'
                }
            })
            
        except Exception as e:
            # Print full traceback for debugging
            print(f"[DEBUG CONFIRM ERROR] {str(e)}")
            print(f"[DEBUG CONFIRM ERROR] Full traceback:")
            traceback.print_exc()
            
            return Response(
                {
                    'error': f'Error confirming payment: {str(e)}',
                    'error_type': type(e).__name__,
                    'session_id': session_id,
                    'request_id': pk
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_summary="Payment Cancelled",
        operation_description="Handle cancelled payment from Stripe checkout.",
        operation_id="request_payment_cancelled",
        tags=['Background Check Payments'],
        responses={
            200: "Payment cancelled"
        }
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny], url_path='payment-cancelled', url_name='payment-cancelled')
    def payment_cancelled(self, request, pk=None):
        """Handle cancelled payment"""
        try:
            bg_request = self.get_object()
            return Response({
                'message': 'Payment was cancelled',
                'request_id': bg_request.id,
                'retry_url': f'/api/requests/api/{bg_request.id}/select-pricing/',
                'note': 'You can try again by selecting a report type'
            })
        except Request.DoesNotExist:
            return Response(
                {'error': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        operation_summary="Get Pricing Options",
        operation_description="Get available pricing options for background check reports.",
        operation_id="request_pricing_options",
        tags=['Background Check Payments'],
        responses={
            200: openapi.Response(
                description="Pricing options",
                examples={
                    "application/json": {
                        "pricing_options": [
                            {
                                "type": "basic",
                                "price": 25.00,
                                "name": "Basic Report",
                                "features": [
                                    "Identity Verification",
                                    "Criminal History Check",
                                    "Address History"
                                ]
                            },
                            {
                                "type": "premium",
                                "price": 50.00,
                                "name": "Premium Report",
                                "features": [
                                    "All Basic features",
                                    "Employment Verification",
                                    "Education Verification",
                                    "Priority Processing"
                                ]
                            }
                        ]
                    }
                }
            )
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='pricing-options', url_name='pricing-options')
    def pricing_options(self, request):
        """Get available pricing options"""
        return Response({
            'pricing_options': [
                {
                    'type': 'basic',
                    'price': 25.00,
                    'name': 'Basic Report',
                    'description': 'Essential background check',
                    'features': [
                        'Identity Verification',
                        'SSN Trace',
                        'National Criminal Search',
                        'Sex Offender Registry',
                        'Address History'
                    ],
                    'delivery': '2-3 business days'
                },
                {
                    'type': 'premium',
                    'price': 50.00,
                    'name': 'Premium Report',
                    'description': 'Comprehensive background check',
                    'features': [
                        'All Basic Report features',
                        'Employment Verification',
                        'Education Verification',
                        'Unlimited County Search',
                        'Priority Processing',
                        'Dedicated Support'
                    ],
                    'delivery': '1-2 business days'
                }
            ]
        })

    @swagger_auto_schema(
        operation_summary="Get Admin Report Form Data",
        operation_description="Get request details and existing report data for admin report submission form. Admin only.",
        operation_id="request_admin_report_form",
        tags=['Admin - Reports'],
        responses={
            200: "Request and report data",
            403: "Admin access required",
            404: "Request not found"
        }
    )
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAdminUser], url_path='admin-report-form', url_name='admin-report-form')
    def get_admin_report_form(self, request, pk=None):
        """Get request details and existing report data for admin form"""
        try:
            bg_request = self.get_object()
            
            # Get existing report if it exists
            report_data = None
            if hasattr(bg_request, 'report'):
                from .serializers import AdminReportFormSerializer
                report_data = AdminReportFormSerializer(bg_request.report).data
            
            return Response({
                'success': True,
                'request': {
                    'id': bg_request.id,
                    'name': bg_request.name,
                    'dob': str(bg_request.dob),
                    'email': bg_request.email,
                    'phone_number': bg_request.phone_number,
                    'city': bg_request.city,
                    'state': bg_request.state,
                    'status': bg_request.status,
                    'created_at': bg_request.created_at.isoformat(),
                    'user': {
                        'id': bg_request.user.id,
                        'username': bg_request.user.username,
                        'email': bg_request.user.email
                    }
                },
                'existing_report': report_data,
                'has_report': hasattr(bg_request, 'report'),
                'form_sections': {
                    'identity_verification': ['ssn_validation', 'address_history', 'identity_cross_reference', 'database_match'],
                    'criminal_history': ['federal_criminal_records', 'state_criminal_records', 'state_searched', 
                                       'county_criminal_records', 'county_searched', 'adult_offender_registry'],
                    'address_history': ['address_history_details'],
                    'education_verification': ['education_verified', 'education_degree', 'education_institution', 
                                              'education_graduation_year', 'education_status'],
                    'employment_verification': ['employment_verified', 'employment_details'],
                    'final_summary': ['final_summary', 'recommendation', 'verification_status']
                }
            })
        except Request.DoesNotExist:
            return Response(
                {'error': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @swagger_auto_schema(
        methods=['post', 'put'],
        operation_summary="Submit Background Check Report (Admin)",
        operation_description="Submit or update a complete background check report. Admin only. Automatically sets request status to 'Completed'. POST creates new report, PUT updates existing.",
        operation_id="request_admin_submit_report",
        tags=['Admin - Reports'],
        responses={
            200: "Report submitted/updated successfully",
            400: "Invalid report data",
            403: "Admin access required",
            404: "Request not found"
        }
    )
    @action(detail=True, methods=['post', 'put'], permission_classes=[permissions.IsAdminUser], url_path='submit-report', url_name='submit-report')
    def submit_admin_report(self, request, pk=None):
        """Submit or update complete background check report from admin"""
        try:
            bg_request = self.get_object()
            from .serializers import AdminReportFormSerializer
            
            # Check if report already exists
            if hasattr(bg_request, 'report'):
                # Update existing report
                serializer = AdminReportFormSerializer(
                    bg_request.report, 
                    data=request.data, 
                    partial=True
                )
            else:
                # Create new report
                # Add request to data
                data = request.data.copy()
                data['request'] = bg_request.id
                serializer = AdminReportFormSerializer(data=data)
            
            if serializer.is_valid():
                report = serializer.save()
                
                # Update request status to Completed
                bg_request.status = 'Completed'
                bg_request.save()
                
                return Response({
                    'success': True,
                    'message': 'Background check report submitted successfully',
                    'report_id': report.id,
                    'request_status': bg_request.status,
                    'report': AdminReportFormSerializer(report).data
                }, status=status.HTTP_201_CREATED if not hasattr(bg_request, 'report') else status.HTTP_200_OK)
            
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Request.DoesNotExist:
            return Response(
                {'error': 'Request not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_summary="Get Pending Reports (Admin)",
        operation_description="Get all background check requests that need reports to be filled out. Admin only.",
        operation_id="request_admin_pending_reports",
        tags=['Admin - Reports'],
        responses={
            200: openapi.Response(
                description="List of pending requests",
                examples={
                    "application/json": {
                        "count": 5,
                        "pending_requests": []
                    }
                }
            ),
            403: "Admin access required"
        }
    )
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser], url_path='pending-reports', url_name='pending-reports')
    def get_pending_reports(self, request):
        """Get all requests that need reports to be filled out"""
        pending_requests = Request.objects.filter(
            status__in=['Pending', 'In Progress']
        ).exclude(
            report__isnull=False
        ).order_by('-created_at')
        
        requests_data = []
        for req in pending_requests:
            requests_data.append({
                'id': req.id,
                'name': req.name,
                'email': req.email,
                'phone_number': req.phone_number,
                'dob': str(req.dob),
                'city': req.city,
                'state': req.state,
                'status': req.status,
                'created_at': req.created_at.isoformat(),
                'days_pending': (timezone.now() - req.created_at).days,
                'user': {
                    'username': req.user.username,
                    'email': req.user.email
                },
                'form_url': f'/api/requests/api/{req.id}/admin-report-form/'
            })
        
        return Response({
            'success': True,
            'count': len(requests_data),
            'requests': requests_data
        })

class ReportViewSet(viewsets.ModelViewSet):
    """
    Background Check Report Management
    
    Allows admins to upload and manage PDF reports for background checks.
    Automatically updates request status to 'Completed' when report is created.
    Users can download their own reports.
    """
    queryset = Report.objects.all().order_by('-generated_at')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['request__status', 'generated_at']
    search_fields = ['request__name', 'request__email', 'notes']

    def get_permissions(self):
        """
        Admin can do everything.
        Users can only download their own reports.
        """
        if self.action == 'download':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_queryset(self):
        """
        Admin sees all reports.
        Users see only their own reports.
        """
        if self.request.user.is_staff:
            return Report.objects.all().order_by('-generated_at')
        return Report.objects.filter(request__user=self.request.user).order_by('-generated_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return ReportCreateSerializer
        return ReportSerializer

    def perform_create(self, serializer):
        report = serializer.save()
        # Automatically update request status to completed
        request_obj = report.request
        request_obj.status = 'Completed'
        request_obj.save()

    @swagger_auto_schema(
        operation_summary="Download Report PDF",
        operation_description="Get download URL for a background check report PDF file. Users can download their own reports, admins can download any report.",
        operation_id="report_download",
        tags=['Reports'],
        responses={
            200: openapi.Response(
                description="Report download URL",
                examples={
                    "application/json": {
                        "success": True,
                        "download_url": "http://localhost:8000/media/reports/report_1.pdf",
                        "filename": "report_1.pdf",
                        "size": 156789
                    }
                }
            ),
            404: "PDF file not available or report not found",
            403: "You don't have permission to download this report"
        }
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download report PDF - Users can download their own reports"""
        try:
            report = self.get_object()
            
            # Check if user has permission (owns the request or is admin)
            if not request.user.is_staff and report.request.user != request.user:
                return Response({
                    'error': 'Permission denied',
                    'message': 'You can only download your own reports'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Check if PDF exists
            if not report.pdf:
                return Response({
                    'error': 'No PDF file available',
                    'message': 'The report has been created but the PDF file is not available yet.'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Check if file physically exists
            try:
                file_size = report.pdf.size
                filename = report.pdf.name.split('/')[-1]
            except (FileNotFoundError, OSError):
                return Response({
                    'error': 'PDF file not found',
                    'message': 'The PDF file is missing from the server. Please contact support.',
                    'report_id': report.id,
                    'request_id': report.request.id
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'success': True,
                'download_url': request.build_absolute_uri(report.pdf.url),
                'filename': filename,
                'size': file_size,
                'size_mb': f"{file_size / (1024 * 1024):.2f} MB",
                'report_id': report.id,
                'request_id': report.request.id,
                'generated_at': report.generated_at
            })
            
        except Report.DoesNotExist:
            return Response({
                'error': 'Report not found'
            }, status=status.HTTP_404_NOT_FOUND)


# ==================== Template-Based Views (MVT Pattern) ====================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def submit_request_view(request):
    """Display form to submit background check request"""
    try:
        subscription = UserSubscription.objects.get(user=request.user)
    except UserSubscription.DoesNotExist:
        messages.error(request, 'You need to select a plan first. Please view available plans.')
        return redirect('subscriptions:plans_list')
    
    # Check if user has a plan assigned
    if not subscription.plan:
        messages.error(request, 'Please select a plan before submitting requests.')
        return redirect('subscriptions:plans_list')
    
    # Check if user can make requests
    if not subscription.can_make_request:
        messages.error(request, 'You have no available reports. Please purchase more reports to continue.')
        return redirect('subscriptions:subscription_dashboard')
    
    if request.method == 'POST':
        try:
            # Create the background check request
            bg_request = Request.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                dob=request.POST.get('dob'),
                email=request.POST.get('email'),
                phone_number=request.POST.get('phone_number'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                status='Pending'
            )
            
            # Increment usage
            subscription.increment_usage()
            
            messages.success(request, f'Background check request submitted successfully! Request ID: {bg_request.id}')
            return redirect('requests:request_success', request_id=bg_request.id)
            
        except Exception as e:
            messages.error(request, f'Error submitting request: {str(e)}')
    
    return render(request, 'requests/submit.html', {
        'subscription': subscription
    })


@login_required
def request_success_view(request, request_id):
    """Display success page after request submission"""
    try:
        bg_request = Request.objects.get(id=request_id, user=request.user)
        return render(request, 'requests/success.html', {
            'request': bg_request
        })
    except Request.DoesNotExist:
        messages.error(request, 'Request not found')
        return redirect('subscriptions:subscription_dashboard')


def payment_success_view(request):
    """Display payment success page with confirmation popup (MTV pattern)"""
    from django.shortcuts import render
    from subscriptions.models import SubscriptionPlan
    
    request_id = request.GET.get('request_id')
    session_id = request.GET.get('session_id')
    
    if not request_id:
        return render(request, 'payment_success.html', {
            'request_id': 'Unknown',
            'plan_name': 'Unknown',
            'amount': '0.00',
            'error': 'Request ID not found'
        })
    
    try:
        bg_request = Request.objects.get(id=request_id)
        
        # Get plan details if available
        plan_name = "Background Check"
        amount = bg_request.payment_amount if bg_request.payment_amount else "0.00"
        
        if bg_request.report_type:
            plan_name = f"{bg_request.report_type.title()} Plan"
        
        return render(request, 'payment_success.html', {
            'request_id': request_id,
            'session_id': session_id,
            'plan_name': plan_name,
            'amount': amount,
            'bg_request': bg_request
        })
    except Request.DoesNotExist:
        return render(request, 'payment_success.html', {
            'request_id': request_id,
            'plan_name': 'Unknown',
            'amount': '0.00',
            'error': 'Request not found'
        })


def payment_cancelled_view(request):
    """Display payment cancelled page"""
    from django.shortcuts import render
    
    request_id = request.GET.get('request_id')
    
    return render(request, 'payment_cancelled.html', {
        'request_id': request_id
    })
