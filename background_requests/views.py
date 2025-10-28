from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
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
        operation_description="Create a new background check request. Requires active subscription.",
        operation_summary="Create Background Check Request",
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
                description="Request created successfully",
                examples={
                    "application/json": {
                        "id": 1,
                        "name": "John Smith",
                        "email": "john.smith@example.com",
                        "phone_number": "+1234567890",
                        "dob": "1990-05-15",
                        "city": "New York",
                        "state": "NY",
                        "status": "Pending",
                        "created_at": "2024-01-20T10:30:00Z"
                    }
                }
            ),
            400: "Bad Request - Validation errors",
            403: "Forbidden - No active subscription or request limit reached"
        },
        tags=['Background Check Requests']
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        # Check if user has active subscription
        try:
            subscription = UserSubscription.objects.get(
                user=self.request.user,
                status='active'
            )
        except UserSubscription.DoesNotExist:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied({
                'error': 'No active subscription',
                'message': 'You need an active subscription to submit background check requests.',
                'action': 'Please subscribe to a plan to continue.',
                'plans_url': '/api/subscriptions/ui/plans/'
            })
        
        # Check if user can make more requests
        if not subscription.can_make_request:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied({
                'error': 'Request limit reached',
                'message': f'You have used all {subscription.plan.max_requests_per_month} requests for this month.',
                'current_usage': subscription.requests_used_this_month,
                'limit': subscription.plan.max_requests_per_month,
                'action': 'Please upgrade your plan or wait until next month.',
                'upgrade_url': '/api/subscriptions/ui/plans/'
            })
        
        # Save the request and increment usage
        request_obj = serializer.save(user=self.request.user)
        subscription.increment_usage()

    def perform_update(self, serializer):
        # Only admins can update status
        if not self.request.user.is_staff:
            # Clients can only update their contact info, not status
            serializer.validated_data.pop('status', None)
        serializer.save()

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
            
            # Return report details with download URL
            return Response({
                'success': True,
                'report': {
                    'id': report.id,
                    'download_url': request.build_absolute_uri(report.pdf.url),
                    'filename': report.pdf.name.split('/')[-1],
                    'generated_at': report.generated_at,
                    'notes': report.notes,
                    'file_size': report.pdf.size if report.pdf else 0,
                    'file_size_mb': f"{report.pdf.size / (1024 * 1024):.2f} MB" if report.pdf else "0 MB"
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
                status=status.HTTP_400_BAD_REQUEST
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
        operation_description="Get user's background check requests dashboard with status tracking",
        operation_summary="User Dashboard - My Requests",
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
        },
        tags=['User Dashboard']
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
                'plan_name': subscription.plan.name,
                'plan_price': str(subscription.plan.price),
                'billing_cycle': subscription.plan.billing_cycle,
                'requests_used': subscription.requests_used_this_month,
                'requests_limit': subscription.plan.max_requests_per_month,
                'requests_remaining': subscription.remaining_requests,
                'status': subscription.status,
                'start_date': subscription.start_date.isoformat() if subscription.start_date else None,
                'end_date': subscription.end_date.isoformat() if subscription.end_date else None,
                'can_make_request': subscription.can_make_request
            }
        except UserSubscription.DoesNotExist:
            subscription_data = {
                'plan_name': None,
                'status': 'inactive',
                'message': 'No active subscription. Please subscribe to a plan.',
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

class ReportViewSet(viewsets.ModelViewSet):
    """
    Background Check Report Management
    
    Allows admins to upload and manage PDF reports for background checks.
    Automatically updates request status to 'Completed' when report is created.
    """
    queryset = Report.objects.all().order_by('-generated_at')
    permission_classes = [permissions.IsAdminUser]  # Only admin can manage reports
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['request__status', 'generated_at']
    search_fields = ['request__name', 'request__email', 'notes']

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

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download report PDF"""
        report = self.get_object()
        if report.pdf:
            return Response({
                'download_url': request.build_absolute_uri(report.pdf.url),
                'filename': report.pdf.name.split('/')[-1],
                'size': report.pdf.size
            })
        return Response(
            {'error': 'No PDF file available'}, 
            status=status.HTTP_404_NOT_FOUND
        )


# ==================== Template-Based Views (MVT Pattern) ====================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def submit_request_view(request):
    """Display form to submit background check request"""
    try:
        subscription = UserSubscription.objects.get(
            user=request.user,
            status='active'
        )
    except UserSubscription.DoesNotExist:
        messages.error(request, 'You need an active subscription to submit requests. Please subscribe to a plan first.')
        return redirect('subscriptions:plans_list')
    
    # Check if user can make requests
    if not subscription.can_make_request:
        messages.error(request, f'You have used all {subscription.plan.max_requests_per_month} requests for this month.')
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
    
    # Calculate usage percentage
    usage_percentage = 0
    if subscription.plan.max_requests_per_month <= 900000:
        usage_percentage = (subscription.requests_used_this_month / subscription.plan.max_requests_per_month) * 100
    
    return render(request, 'requests/submit.html', {
        'subscription': subscription,
        'usage_percentage': min(usage_percentage, 100)
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
