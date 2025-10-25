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
