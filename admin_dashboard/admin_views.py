from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import action
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.utils import timezone
from background_requests.models import Request, Report
from .models import AdminDashboardSettings, RequestActivity, AdminNote, RequestAssignment
from .serializers import (
    AdminRequestSerializer, AdminReportSerializer, AdminDashboardSettingsSerializer,
    RequestActivitySerializer, AdminNoteSerializer, RequestAssignmentSerializer,
    StatusUpdateSerializer, BulkStatusUpdateSerializer, DashboardStatsSerializer,
    AdminUserSerializer
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()

class AdminDashboardStatsView(APIView):
    """View for dashboard statistics and overview"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get Dashboard Statistics",
        operation_description="Get system overview including total requests, pending/in-progress/completed counts, total clients, recent requests and activities.",
        operation_id="admin_dashboard_stats",
        tags=['Admin - Dashboard'],
        responses={
            200: DashboardStatsSerializer,
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request):
        # Get counts
        total_requests = Request.objects.count()
        pending_requests = Request.objects.filter(status='Pending').count()
        in_progress_requests = Request.objects.filter(status='In Progress').count()
        completed_requests = Request.objects.filter(status='Completed').count()
        total_clients = User.objects.filter(is_staff=False).count()
        
        # Get recent requests (last 10)
        recent_requests = Request.objects.all().order_by('-created_at')[:10]
        
        # Get recent activities (last 10)
        recent_activities = RequestActivity.objects.all().order_by('-timestamp')[:10]
        
        data = {
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'in_progress_requests': in_progress_requests,
            'completed_requests': completed_requests,
            'total_clients': total_clients,
            'recent_requests': recent_requests,
            'recent_activities': recent_activities
        }
        
        serializer = DashboardStatsSerializer(data)
        return Response(serializer.data)

class AdminRequestManagementView(APIView):
    """Enhanced request management with filtering and bulk operations"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Manage All Requests",
        operation_description="Get all background check requests with optional filtering by status, assigned admin, or search query.",
        operation_id="admin_requests_list",
        tags=['Admin - Request Management'],
        manual_parameters=[
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by status (Pending, In Progress, Completed)", type=openapi.TYPE_STRING),
            openapi.Parameter('assigned_to', openapi.IN_QUERY, description="Filter by assigned admin user ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by name, email, or username", type=openapi.TYPE_STRING),
        ],
        responses={
            200: AdminRequestSerializer(many=True),
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request):
        # Get query parameters for filtering
        status_filter = request.query_params.get('status', None)
        assigned_to = request.query_params.get('assigned_to', None)
        search = request.query_params.get('search', None)
        
        queryset = Request.objects.all().order_by('-created_at')
        
        # Apply filters
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if assigned_to:
            queryset = queryset.filter(assignment__assigned_to=assigned_to)
        
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(user__username__icontains=search)
            )
        
        serializer = AdminRequestSerializer(queryset, many=True)
        return Response(serializer.data)

class AdminRequestDetailView(APIView):
    """Detailed view for individual requests with activities and notes"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get Request Details",
        operation_description="Get detailed information for a specific request including activities, notes, and assignment.",
        operation_id="admin_request_detail",
        tags=['Admin - Request Management'],
        responses={
            200: openapi.Response(
                description="Request details with activities and notes",
                examples={
                    "application/json": {
                        "request": {"id": 1, "name": "John Doe", "status": "Pending"},
                        "activities": [],
                        "notes": [],
                        "assignment": None
                    }
                }
            ),
            404: "Request not found",
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request, request_id):
        try:
            bg_request = Request.objects.get(id=request_id)
            
            # Get request details
            request_data = AdminRequestSerializer(bg_request).data
            
            # Get activities
            activities = RequestActivity.objects.filter(request=bg_request).order_by('-timestamp')
            activities_data = RequestActivitySerializer(activities, many=True).data
            
            # Get notes
            notes = AdminNote.objects.filter(request=bg_request).order_by('-created_at')
            notes_data = AdminNoteSerializer(notes, many=True).data
            
            # Get assignment
            assignment_data = None
            if hasattr(bg_request, 'assignment'):
                assignment_data = RequestAssignmentSerializer(bg_request.assignment).data
            
            return Response({
                'request': request_data,
                'activities': activities_data,
                'notes': notes_data,
                'assignment': assignment_data
            })
            
        except Request.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

class AdminStatusUpdateView(APIView):
    """Update request status with activity logging"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Update Request Status",
        operation_description="Change the status of a background check request. Automatically logs the activity and optionally adds admin notes.",
        operation_id="admin_request_update_status",
        tags=['Admin - Request Management'],
        request_body=StatusUpdateSerializer,
        responses={
            200: AdminRequestSerializer,
            400: "Bad Request - Invalid status",
            404: "Request not found",
            403: "Forbidden - Admin access required"
        }
    )
    def patch(self, request, request_id):
        try:
            bg_request = Request.objects.get(id=request_id)
            serializer = StatusUpdateSerializer(data=request.data)
            
            if serializer.is_valid():
                old_status = bg_request.status
                new_status = serializer.validated_data['status']
                notes = serializer.validated_data.get('notes', '')
                
                # Update status
                bg_request.status = new_status
                bg_request.save()
                
                # Log activity
                RequestActivity.objects.create(
                    request=bg_request,
                    admin_user=request.user,
                    activity_type='status_change',
                    description=f'Status changed from {old_status} to {new_status}',
                    old_value=old_status,
                    new_value=new_status
                )
                
                # Add note if provided
                if notes:
                    AdminNote.objects.create(
                        request=bg_request,
                        admin_user=request.user,
                        note=notes,
                        is_internal=True
                    )
                
                return Response({
                    'message': 'Status updated successfully',
                    'request': AdminRequestSerializer(bg_request).data
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Request.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

class AdminBulkStatusUpdateView(APIView):
    """Bulk update request statuses"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Bulk Update Request Status",
        operation_description="Update the status of multiple requests at once. Automatically logs activities for each updated request.",
        operation_id="admin_requests_bulk_update",
        tags=['Admin - Request Management'],
        request_body=BulkStatusUpdateSerializer,
        responses={
            200: openapi.Response(
                description="Requests updated successfully",
                examples={
                    "application/json": {
                        "message": "Successfully updated 5 requests",
                        "count": 5
                    }
                }
            ),
            400: "Bad Request - Invalid data",
            403: "Forbidden - Admin access required"
        }
    )
    def patch(self, request):
        serializer = BulkStatusUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            request_ids = serializer.validated_data['request_ids']
            new_status = serializer.validated_data['status']
            notes = serializer.validated_data.get('notes', '')
            
            updated_requests = []
            
            for request_id in request_ids:
                try:
                    bg_request = Request.objects.get(id=request_id)
                    old_status = bg_request.status
                    
                    bg_request.status = new_status
                    bg_request.save()
                    
                    # Log activity
                    RequestActivity.objects.create(
                        request=bg_request,
                        admin_user=request.user,
                        activity_type='status_change',
                        description=f'Bulk status change from {old_status} to {new_status}',
                        old_value=old_status,
                        new_value=new_status
                    )
                    
                    updated_requests.append(bg_request)
                    
                except Request.DoesNotExist:
                    continue
            
            return Response({
                'message': f'Updated {len(updated_requests)} requests',
                'updated_count': len(updated_requests)
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminNoteView(APIView):
    """Manage admin notes for requests"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Add Admin Note to Request",
        operation_description="Add an internal or public note to a specific request. Internal notes are only visible to admins.",
        operation_id="admin_request_add_note",
        tags=['Admin - Request Management'],
        request_body=AdminNoteSerializer,
        responses={
            201: AdminNoteSerializer,
            400: "Bad Request - Invalid note data",
            404: "Request not found",
            403: "Forbidden - Admin access required"
        }
    )
    def post(self, request, request_id):
        try:
            bg_request = Request.objects.get(id=request_id)
            serializer = AdminNoteSerializer(data=request.data)
            
            if serializer.is_valid():
                note = serializer.save(
                    request=bg_request,
                    admin_user=request.user
                )
                
                # Log activity
                RequestActivity.objects.create(
                    request=bg_request,
                    admin_user=request.user,
                    activity_type='comment_added',
                    description=f'Added {"internal" if note.is_internal else "public"} note'
                )
                
                return Response(AdminNoteSerializer(note).data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Request.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)

class AdminAssignmentView(APIView):
    """Manage request assignments"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Assign Request to Admin",
        operation_description="Assign a background check request to a specific admin user for processing.",
        operation_id="admin_request_assign",
        tags=['Admin - Request Management'],
        request_body=RequestAssignmentSerializer,
        responses={
            201: RequestAssignmentSerializer,
            400: "Bad Request - Invalid assignment data",
            404: "Request not found",
            403: "Forbidden - Admin access required"
        }
    )
    def post(self, request, request_id):
        try:
            bg_request = Request.objects.get(id=request_id)
            
            # Check if already assigned
            if hasattr(bg_request, 'assignment'):
                return Response({'error': 'Request already assigned. Use PATCH to update the assignment.'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Validate that assigned_to user exists
            assigned_to_id = request.data.get('assigned_to')
            if not assigned_to_id:
                return Response({'error': 'assigned_to field is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                assigned_user = User.objects.get(id=assigned_to_id)
                if not assigned_user.is_staff:
                    return Response({
                        'error': f'User "{assigned_user.username}" (ID: {assigned_to_id}) is not an admin user. Only staff members can be assigned requests.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({
                    'error': f'User with ID {assigned_to_id} does not exist. Please provide a valid admin user ID.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = RequestAssignmentSerializer(data=request.data)
            
            if serializer.is_valid():
                assignment = serializer.save(
                    request=bg_request,
                    assigned_by=request.user
                )
                
                # Log activity
                RequestActivity.objects.create(
                    request=bg_request,
                    admin_user=request.user,
                    activity_type='request_assigned',
                    description=f'Request assigned to {assignment.assigned_to.username}'
                )
                
                return Response(RequestAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Request.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Update Request Assignment",
        operation_description="Update the assignment of a request to a different admin user.",
        operation_id="admin_request_reassign",
        tags=['Admin - Request Management'],
        request_body=RequestAssignmentSerializer,
        responses={
            200: RequestAssignmentSerializer,
            400: "Bad Request - Invalid assignment data",
            404: "Request or assignment not found",
            403: "Forbidden - Admin access required"
        }
    )
    def patch(self, request, request_id):
        try:
            bg_request = Request.objects.get(id=request_id)
            assignment = bg_request.assignment
            
            serializer = RequestAssignmentSerializer(assignment, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                
                # Log activity
                RequestActivity.objects.create(
                    request=bg_request,
                    admin_user=request.user,
                    activity_type='request_assigned',
                    description=f'Assignment updated'
                )
                
                return Response(serializer.data)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Request.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)
        except RequestAssignment.DoesNotExist:
            return Response({'error': 'Request not assigned'}, status=status.HTTP_404_NOT_FOUND)

class AdminUsersView(APIView):
    """Manage admin users and their assignments"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get All Admin Users",
        operation_description="Get list of all admin/staff users in the system.",
        operation_id="admin_users_list",
        tags=['Admin - User Management'],
        responses={
            200: AdminUserSerializer(many=True),
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request):
        admin_users = User.objects.filter(is_staff=True)
        serializer = AdminUserSerializer(admin_users, many=True)
        return Response(serializer.data)


class AdminAllUsersView(APIView):
    """Get all regular users (non-admin)"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get All Users",
        operation_description="Get list of all regular users with their subscription information.",
        operation_id="admin_all_users_list",
        tags=['Admin - User Management'],
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search by name or email", type=openapi.TYPE_STRING),
            openapi.Parameter('subscription_plan', openapi.IN_QUERY, description="Filter by plan name", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description="List of users",
                examples={
                    "application/json": {
                        "count": 10,
                        "results": []
                    }
                }
            ),
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request):
        from subscriptions.models import UserSubscription
        
        search = request.query_params.get('search', None)
        subscription_plan = request.query_params.get('subscription_plan', None)
        
        queryset = User.objects.filter(is_staff=False).select_related('subscription')
        
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        users_data = []
        for user in queryset:
            # Use the select_related subscription if available
            try:
                subscription = user.subscription
                user_data = {
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'email': user.email,
                    'subscription_plan': subscription.plan.name if subscription.plan else 'No Plan',
                    'start_date': user.date_joined.strftime('%Y-%m-%d'),
                    'requests': Request.objects.filter(user=user).count(),
                    'total_reports_purchased': subscription.total_reports_purchased,
                    'total_reports_used': subscription.total_reports_used,
                    'available_reports': subscription.available_reports,
                    'status': 'active' if subscription.plan else 'inactive'
                }
            except UserSubscription.DoesNotExist:
                user_data = {
                    'id': user.id,
                    'name': f"{user.first_name} {user.last_name}".strip() or user.username,
                    'email': user.email,
                    'subscription_plan': 'No Plan',
                    'start_date': user.date_joined.strftime('%Y-%m-%d'),
                    'requests': Request.objects.filter(user=user).count(),
                    'total_reports_purchased': 0,
                    'total_reports_used': 0,
                    'available_reports': 0,
                    'status': 'inactive'
                }
            
            users_data.append(user_data)
        
        return Response({
            'count': len(users_data),
            'results': users_data
        })


class AdminUserDetailView(APIView):
    """Get single user detail"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get Single User Details",
        operation_description="Get detailed information about a specific user including subscription and requests.",
        operation_id="admin_user_detail",
        tags=['Admin - User Management'],
        responses={
            200: openapi.Response(
                description="User details",
                examples={
                    "application/json": {
                        "id": 1,
                        "username": "johndoe",
                        "email": "john@example.com",
                        "subscription": {},
                        "requests": []
                    }
                }
            ),
            404: "User not found",
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request, user_id):
        try:
            from subscriptions.models import UserSubscription
            from subscriptions.serializers import UserSubscriptionSerializer
            from background_requests.serializers import RequestSerializer
            
            user = User.objects.get(id=user_id)
            
            # Get subscription
            subscription_data = None
            try:
                subscription = UserSubscription.objects.get(user=user)
                subscription_data = UserSubscriptionSerializer(subscription).data
            except UserSubscription.DoesNotExist:
                pass
            
            # Get requests
            requests = Request.objects.filter(user=user).order_by('-created_at')[:10]
            requests_data = RequestSerializer(requests, many=True).data
            
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
                'subscription': subscription_data,
                'requests': requests_data,
                'date_joined': user.date_joined
            }
            
            return Response(user_data)
            
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)


class AdminReportDownloadView(APIView):
    """Download report PDF"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Download Report PDF",
        operation_description="Download the PDF report for a specific request.",
        operation_id="admin_report_download",
        tags=['Admin - Report Management'],
        responses={
            200: "PDF file",
            404: "Report not found",
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request, request_id):
        from django.http import FileResponse, Http404
        import os
        
        try:
            bg_request = Request.objects.get(id=request_id)
            
            if not hasattr(bg_request, 'report') or not bg_request.report:
                return Response({'error': 'Report not found for this request'}, status=status.HTTP_404_NOT_FOUND)
            
            report = bg_request.report
            
            if not report.pdf:
                return Response({'error': 'PDF file not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Open the file
            try:
                response = FileResponse(report.pdf.open('rb'), content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="report_{request_id}.pdf"'
                return response
            except FileNotFoundError:
                return Response({'error': 'PDF file does not exist'}, status=status.HTTP_404_NOT_FOUND)
            
        except Request.DoesNotExist:
            return Response({'error': 'Request not found'}, status=status.HTTP_404_NOT_FOUND)


class AdminPlanManagementView(APIView):
    """Admin CRUD operations for subscription plans"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get All Plans",
        operation_description="Get list of subscription plans. By default returns only active plans. Use ?include_inactive=true to see all plans.",
        operation_id="admin_plans_list",
        tags=['Admin - Plan Management'],
        manual_parameters=[
            openapi.Parameter('include_inactive', openapi.IN_QUERY, description="Set to 'true' to include inactive/deleted plans", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: openapi.Response(
                description="List of plans",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "name": "Basic Plan",
                            "price_per_report": "25.00",
                            "is_active": True
                        }
                    ]
                }
            ),
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request):
        from subscriptions.models import SubscriptionPlan
        from subscriptions.serializers import SubscriptionPlanSerializer
        
        # By default, only show active plans
        include_inactive = request.query_params.get('include_inactive', 'false').lower() == 'true'
        
        if include_inactive:
            plans = SubscriptionPlan.objects.all().order_by('-is_active', 'price_per_report')
        else:
            plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_per_report')
        
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response({
            'plans': serializer.data,
            'count': len(serializer.data),
            'showing_inactive': include_inactive
        })
    
    @swagger_auto_schema(
        operation_summary="Create New Plan",
        operation_description="Create a new subscription plan.",
        operation_id="admin_plans_create",
        tags=['Admin - Plan Management'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'price_per_report', 'description'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Plan name'),
                'plan_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['basic', 'premium'], description='Plan type'),
                'price_per_report': openapi.Schema(type=openapi.TYPE_NUMBER, description='Price per report'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Plan description'),
                'identity_verification': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                'ssn_trace': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                'national_criminal_search': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                'sex_offender_registry': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                'employment_verification': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                'education_verification': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                'unlimited_county_search': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                'priority_support': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
                'api_access': openapi.Schema(type=openapi.TYPE_BOOLEAN, default=False),
            }
        ),
        responses={
            201: "Plan created successfully",
            400: "Invalid data",
            403: "Forbidden - Admin access required"
        }
    )
    def post(self, request):
        from subscriptions.models import SubscriptionPlan
        from subscriptions.serializers import SubscriptionPlanSerializer
        
        serializer = SubscriptionPlanSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminPlanDetailView(APIView):
    """Update or delete a specific plan"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get Plan Details",
        operation_description="Get details of a specific plan.",
        operation_id="admin_plan_detail",
        tags=['Admin - Plan Management'],
        responses={
            200: "Plan details",
            404: "Plan not found",
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request, plan_id):
        from subscriptions.models import SubscriptionPlan
        from subscriptions.serializers import SubscriptionPlanSerializer
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            serializer = SubscriptionPlanSerializer(plan)
            return Response(serializer.data)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Update Plan",
        operation_description="Update an existing subscription plan.",
        operation_id="admin_plan_update",
        tags=['Admin - Plan Management'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Plan name'),
                'plan_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['basic', 'premium']),
                'price_per_report': openapi.Schema(type=openapi.TYPE_NUMBER, description='Price per report'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Plan description'),
                'identity_verification': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'ssn_trace': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'national_criminal_search': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'sex_offender_registry': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'employment_verification': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'education_verification': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'unlimited_county_search': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'priority_support': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'api_access': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            }
        ),
        responses={
            200: "Plan updated successfully",
            400: "Invalid data",
            404: "Plan not found",
            403: "Forbidden - Admin access required"
        }
    )
    def patch(self, request, plan_id):
        from subscriptions.models import SubscriptionPlan
        from subscriptions.serializers import SubscriptionPlanSerializer
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            serializer = SubscriptionPlanSerializer(plan, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @swagger_auto_schema(
        operation_summary="Delete Plan",
        operation_description="Delete a subscription plan. Use ?hard_delete=true for permanent deletion, otherwise does soft delete (sets is_active=False).",
        operation_id="admin_plan_delete",
        tags=['Admin - Plan Management'],
        manual_parameters=[
            openapi.Parameter('hard_delete', openapi.IN_QUERY, description="Set to 'true' for permanent deletion", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: "Plan deleted successfully",
            400: "Cannot delete - plan has active subscriptions",
            404: "Plan not found",
            403: "Forbidden - Admin access required"
        }
    )
    def delete(self, request, plan_id):
        from subscriptions.models import SubscriptionPlan, UserSubscription
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Check if plan has active subscriptions
            active_subscriptions = UserSubscription.objects.filter(plan=plan).count()
            
            hard_delete = request.query_params.get('hard_delete', 'false').lower() == 'true'
            
            if hard_delete:
                if active_subscriptions > 0:
                    return Response({
                        'error': f'Cannot delete plan. {active_subscriptions} users are currently subscribed to this plan.',
                        'active_subscriptions': active_subscriptions
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Perform hard delete
                plan_name = plan.name
                plan.delete()
                return Response({
                    'message': f'Plan "{plan_name}" permanently deleted',
                    'deleted': True
                })
            else:
                # Soft delete - just deactivate
                plan.is_active = False
                plan.save()
                return Response({
                    'message': f'Plan "{plan.name}" deactivated (soft delete)',
                    'is_active': False,
                    'note': 'Use ?hard_delete=true to permanently delete this plan'
                })
                
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)


class AdminPlanToggleStatusView(APIView):
    """Toggle plan active/inactive status"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Toggle Plan Status",
        operation_description="Toggle plan active/inactive status.",
        operation_id="admin_plan_toggle_status",
        tags=['Admin - Plan Management'],
        responses={
            200: "Status toggled successfully",
            404: "Plan not found",
            403: "Forbidden - Admin access required"
        }
    )
    def post(self, request, plan_id):
        from subscriptions.models import SubscriptionPlan
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            plan.is_active = not plan.is_active
            plan.save()
            return Response({
                'message': f'Plan {"activated" if plan.is_active else "deactivated"} successfully',
                'is_active': plan.is_active
            })
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)


class AdminNotificationView(APIView):
    """Admin notification management"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get Admin Notifications",
        operation_description="Get all notifications for admin users.",
        operation_id="admin_notifications_list",
        tags=['Admin - Notifications'],
        manual_parameters=[
            openapi.Parameter('unread_only', openapi.IN_QUERY, description="Filter unread only", type=openapi.TYPE_BOOLEAN),
        ],
        responses={
            200: openapi.Response(
                description="List of notifications",
                examples={
                    "application/json": {
                        "count": 5,
                        "unread_count": 2,
                        "results": []
                    }
                }
            ),
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request):
        from notifications.models import Notification
        from notifications.serializers import NotificationSerializer
        
        unread_only = request.query_params.get('unread_only', 'false').lower() == 'true'
        
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        
        if unread_only:
            notifications = notifications.filter(is_read=False)
        
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        
        serializer = NotificationSerializer(notifications, many=True)
        
        return Response({
            'count': notifications.count(),
            'unread_count': unread_count,
            'results': serializer.data
        })


class AdminNotificationMarkReadView(APIView):
    """Mark single notification as read"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Mark Notification as Read",
        operation_description="Mark a specific notification as read.",
        operation_id="admin_notification_mark_read",
        tags=['Admin - Notifications'],
        responses={
            200: "Notification marked as read",
            404: "Notification not found",
            403: "Forbidden - Admin access required"
        }
    )
    def post(self, request, notification_id):
        from notifications.models import Notification
        
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save()
            return Response({'message': 'Notification marked as read'})
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)


class AdminNotificationMarkAllReadView(APIView):
    """Mark all notifications as read"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Mark All Notifications as Read",
        operation_description="Mark all notifications as read for the current admin user.",
        operation_id="admin_notification_mark_all_read",
        tags=['Admin - Notifications'],
        responses={
            200: "All notifications marked as read",
            403: "Forbidden - Admin access required"
        }
    )
    def post(self, request):
        from notifications.models import Notification
        
        updated_count = Notification.objects.filter(
            recipient=request.user, 
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({
            'message': f'{updated_count} notifications marked as read',
            'count': updated_count
        })


class AdminPaymentHistoryView(APIView):
    """View all payment transactions across all users"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get All Payment Transactions",
        operation_description="Get list of all payment transactions across all users with filtering options.",
        operation_id="admin_payment_history",
        tags=['Admin - Payments'],
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, description="Filter by user ID", type=openapi.TYPE_INTEGER),
            openapi.Parameter('status', openapi.IN_QUERY, description="Filter by payment status (succeeded, pending, failed, canceled, refunded)", type=openapi.TYPE_STRING),
            openapi.Parameter('start_date', openapi.IN_QUERY, description="Filter payments after this date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
            openapi.Parameter('end_date', openapi.IN_QUERY, description="Filter payments before this date (YYYY-MM-DD)", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response(
                description="List of payment transactions",
                examples={
                    "application/json": {
                        "count": 50,
                        "total_amount": "1250.00",
                        "payments": [
                            {
                                "id": 1,
                                "user": {
                                    "id": 42,
                                    "username": "john_doe",
                                    "email": "john@example.com"
                                },
                                "plan": "Basic Plan",
                                "amount": "25.00",
                                "currency": "USD",
                                "status": "succeeded",
                                "reports_purchased": 10,
                                "stripe_payment_intent_id": "pi_abc123",
                                "created_at": "2024-11-12T10:30:00Z"
                            }
                        ]
                    }
                }
            ),
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request):
        from subscriptions.models import PaymentHistory
        from decimal import Decimal
        
        # Get query parameters
        user_id = request.query_params.get('user_id')
        payment_status = request.query_params.get('status')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Base queryset
        payments = PaymentHistory.objects.select_related('user', 'plan').all()
        
        # Apply filters
        if user_id:
            payments = payments.filter(user_id=user_id)
        if payment_status:
            payments = payments.filter(status=payment_status)
        if start_date:
            payments = payments.filter(created_at__gte=start_date)
        if end_date:
            payments = payments.filter(created_at__lte=end_date)
        
        # Order by most recent
        payments = payments.order_by('-created_at')
        
        # Calculate totals
        total_amount = sum(payment.amount for payment in payments)
        
        # Serialize data
        payments_data = []
        for payment in payments:
            payments_data.append({
                'id': payment.id,
                'user': {
                    'id': payment.user.id,
                    'username': payment.user.username,
                    'email': payment.user.email,
                    'full_name': f"{payment.user.first_name} {payment.user.last_name}".strip() or payment.user.username
                },
                'plan': payment.plan.name if payment.plan else None,
                'amount': str(payment.amount),
                'currency': payment.currency,
                'status': payment.status,
                'reports_purchased': payment.reports_purchased,
                'description': payment.description,
                'stripe_payment_intent_id': payment.stripe_payment_intent_id,
                'stripe_charge_id': payment.stripe_charge_id,
                'failure_reason': payment.failure_reason,
                'created_at': payment.created_at,
                'updated_at': payment.updated_at
            })
        
        return Response({
            'count': len(payments_data),
            'total_amount': str(total_amount),
            'filters_applied': {
                'user_id': user_id,
                'status': payment_status,
                'start_date': start_date,
                'end_date': end_date
            },
            'payments': payments_data
        })


class AdminSubscriptionAnalyticsView(APIView):
    """Get subscription and payment analytics"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get Subscription Analytics",
        operation_description="Get comprehensive analytics including revenue, active subscriptions, popular plans, etc.",
        operation_id="admin_subscription_analytics",
        tags=['Admin - Payments'],
        responses={
            200: openapi.Response(
                description="Analytics data",
                examples={
                    "application/json": {
                        "total_revenue": "15000.00",
                        "active_subscriptions": 150,
                        "total_transactions": 500,
                        "popular_plans": [],
                        "revenue_by_month": []
                    }
                }
            ),
            403: "Forbidden - Admin access required"
        }
    )
    def get(self, request):
        from subscriptions.models import PaymentHistory, UserSubscription, SubscriptionPlan
        from django.db.models import Sum, Count
        from django.db.models.functions import TruncMonth
        from decimal import Decimal
        
        # Total revenue
        total_revenue = PaymentHistory.objects.filter(status='succeeded').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        # Active subscriptions count (users with plans)
        active_subscriptions = UserSubscription.objects.filter(plan__isnull=False).count()
        
        # Total transactions
        total_transactions = PaymentHistory.objects.count()
        successful_transactions = PaymentHistory.objects.filter(status='succeeded').count()
        failed_transactions = PaymentHistory.objects.filter(status='failed').count()
        
        # Popular plans
        popular_plans = SubscriptionPlan.objects.annotate(
            subscriber_count=Count('usersubscription'),
            total_revenue=Sum('paymenthistory__amount', filter=Q(paymenthistory__status='succeeded'))
        ).order_by('-subscriber_count')[:5]
        
        popular_plans_data = []
        for plan in popular_plans:
            popular_plans_data.append({
                'id': plan.id,
                'name': plan.name,
                'price_per_report': str(plan.price_per_report),
                'subscribers': plan.subscriber_count,
                'revenue': str(plan.total_revenue or Decimal('0.00'))
            })
        
        # Revenue by month (last 12 months)
        revenue_by_month = PaymentHistory.objects.filter(
            status='succeeded',
            created_at__gte=timezone.now() - timezone.timedelta(days=365)
        ).annotate(
            month=TruncMonth('created_at')
        ).values('month').annotate(
            revenue=Sum('amount'),
            transactions=Count('id')
        ).order_by('month')
        
        revenue_by_month_data = []
        for item in revenue_by_month:
            revenue_by_month_data.append({
                'month': item['month'].strftime('%Y-%m'),
                'revenue': str(item['revenue']),
                'transactions': item['transactions']
            })
        
        # Recent large transactions
        recent_large_transactions = PaymentHistory.objects.filter(
            status='succeeded',
            amount__gte=Decimal('50.00')
        ).select_related('user', 'plan').order_by('-created_at')[:10]
        
        large_transactions_data = []
        for payment in recent_large_transactions:
            large_transactions_data.append({
                'id': payment.id,
                'user': payment.user.username,
                'amount': str(payment.amount),
                'plan': payment.plan.name if payment.plan else None,
                'reports_purchased': payment.reports_purchased,
                'created_at': payment.created_at
            })
        
        return Response({
            'overview': {
                'total_revenue': str(total_revenue),
                'active_subscriptions': active_subscriptions,
                'total_transactions': total_transactions,
                'successful_transactions': successful_transactions,
                'failed_transactions': failed_transactions,
                'success_rate': f"{(successful_transactions/total_transactions*100):.1f}%" if total_transactions > 0 else "0%"
            },
            'popular_plans': popular_plans_data,
            'revenue_by_month': revenue_by_month_data,
            'recent_large_transactions': large_transactions_data
        })