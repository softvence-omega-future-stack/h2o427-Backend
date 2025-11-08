from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.decorators import action
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
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
            'recent_requests': AdminRequestSerializer(recent_requests, many=True).data,
            'recent_activities': RequestActivitySerializer(recent_activities, many=True).data
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
                return Response({'error': 'Request already assigned'}, status=status.HTTP_400_BAD_REQUEST)
            
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