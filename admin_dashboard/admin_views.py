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

User = get_user_model()

class AdminDashboardStatsView(APIView):
    """View for dashboard statistics and overview"""
    permission_classes = [permissions.IsAdminUser]
    
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
    
    def get(self, request):
        admin_users = User.objects.filter(is_staff=True)
        serializer = AdminUserSerializer(admin_users, many=True)
        return Response(serializer.data)