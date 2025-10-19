from rest_framework import viewsets, status, permissions, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Request, Report
from .serializers import (
    RequestSerializer, RequestCreateSerializer, RequestListSerializer, 
    RequestUpdateSerializer, ReportSerializer, ReportCreateSerializer
)

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

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # Only admins can update status
        if not self.request.user.is_staff:
            # Clients can only update their contact info, not status
            serializer.validated_data.pop('status', None)
        serializer.save()

    @action(detail=True, methods=['get'])
    def download_report(self, request, pk=None):
        """Allow clients to download their background check report"""
        try:
            bg_request = self.get_object()
            if hasattr(bg_request, 'report') and bg_request.report.pdf:
                report = bg_request.report
                return Response({
                    'report_url': request.build_absolute_uri(report.pdf.url),
                    'generated_at': report.generated_at,
                    'notes': report.notes,
                    'file_size': report.pdf.size if report.pdf else 0
                })
            else:
                return Response(
                    {'message': 'Report not available yet'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['patch'], permission_classes=[permissions.IsAdminUser])
    def update_status(self, request, pk=None):
        """Update request status (admin only)"""
        bg_request = self.get_object()
        serializer = RequestUpdateSerializer(bg_request, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': f'Status updated to {serializer.validated_data["status"]}',
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
