from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from background_requests.models import Request, Report
from .serializers import AdminRequestSerializer, AdminReportSerializer

class AdminRequestView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get all background check requests with admin access. Returns complete list with user details and status.",
        operation_summary="Get All Background Check Requests",
        operation_id="admin_all_requests",
        responses={
            200: openapi.Response(
                description="List of all background check requests",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "user": {"id": 2, "email": "user@example.com"},
                            "name": "John Smith",
                            "email": "john.smith@example.com",
                            "status": "pending",
                            "created_at": "2024-01-20T10:30:00Z"
                        }
                    ]
                }
            ),
            403: "Forbidden - Admin only"
        },
        tags=['Admin - Reports']
    )
    def get(self, request):
        """Get all background check requests for admin dashboard"""
        requests = Request.objects.all().order_by('-created_at')
        serializer = AdminRequestSerializer(requests, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Update the status of a background check request. Admin only. Valid statuses: Pending, In Progress, Completed.",
        operation_summary="Change Request Status",
        operation_id="admin_update_request_status",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['request_id', 'status'],
            properties={
                'request_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Background check request ID', example=1),
                'status': openapi.Schema(type=openapi.TYPE_STRING, description='New status', enum=['Pending', 'In Progress', 'Completed'], example='In Progress'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Status updated successfully",
                examples={
                    "application/json": {
                        "message": "Status updated successfully",
                        "request": {
                            "id": 1,
                            "status": "In Progress"
                        }
                    }
                }
            ),
            400: "Bad Request - Invalid status",
            403: "Forbidden - Admin only",
            404: "Not Found - Request not found"
        },
        tags=['Admin - Reports']
    )
    def patch(self, request, request_id=None):
        """Update request status"""
        try:
            if not request_id:
                request_id = request.data.get('request_id')
            
            bg_request = Request.objects.get(id=request_id)
            new_status = request.data.get('status')
            
            if new_status in ['Pending', 'In Progress', 'Completed']:
                bg_request.status = new_status
                bg_request.save()
                
                serializer = AdminRequestSerializer(bg_request)
                return Response({
                    'message': 'Status updated successfully',
                    'request': serializer.data
                })
            else:
                return Response(
                    {'error': 'Invalid status'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Request.DoesNotExist:
            return Response(
                {'error': 'Request not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class AdminReportView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Upload a PDF report for a completed background check. Admin only. Automatically sets request status to 'Completed'.",
        operation_summary="Upload Background Check Report",
        operation_id="admin_upload_report",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['request_id', 'pdf'],
            properties={
                'request_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Background check request ID', example=1),
                'pdf': openapi.Schema(type=openapi.TYPE_FILE, description='PDF report file'),
                'notes': openapi.Schema(type=openapi.TYPE_STRING, description='Additional notes', example='Background check completed with no issues'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Report uploaded successfully",
                examples={
                    "application/json": {
                        "message": "Report uploaded successfully",
                        "report": {
                            "id": 1,
                            "request_id": 1,
                            "pdf": "/media/reports/report_1.pdf",
                            "notes": "Background check completed",
                            "generated_at": "2024-01-20T15:30:00Z"
                        }
                    }
                }
            ),
            400: "Bad Request - Missing required fields",
            403: "Forbidden - Admin only",
            404: "Not Found - Request not found"
        },
        tags=['Admin - Reports']
    )
    def post(self, request):
        """Upload or generate PDF report for a background check request"""
        try:
            request_id = request.data.get('request_id')
            # Accept both 'pdf' and 'report_file' for backward compatibility
            pdf_file = request.FILES.get('pdf') or request.FILES.get('report_file')
            notes = request.data.get('notes', '')
            
            if not request_id:
                return Response(
                    {'error': 'request_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            bg_request = Request.objects.get(id=request_id)
            
            # Check if report already exists
            if hasattr(bg_request, 'report'):
                # Update existing report
                report = bg_request.report
                if pdf_file:
                    report.pdf = pdf_file
                report.notes = notes
                report.save()
                message = 'Report updated successfully'
            else:
                # Create new report
                if not pdf_file:
                    return Response(
                        {'error': 'PDF file is required'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                report = Report.objects.create(
                    request=bg_request,
                    pdf=pdf_file,
                    notes=notes
                )
                message = 'Report uploaded successfully'
            
            # Update request status to completed
            bg_request.status = 'Completed'
            bg_request.save()
            
            serializer = AdminReportSerializer(report)
            return Response({
                'message': message,
                'report': serializer.data
            })
            
        except Request.DoesNotExist:
            return Response(
                {'error': 'Request not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        operation_description="Get all generated reports with request details. Admin only.",
        operation_summary="Get All Generated Reports",
        operation_id="admin_all_reports",
        responses={
            200: openapi.Response(
                description="List of all reports",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "request_id": 1,
                            "pdf": "/media/reports/report_1.pdf",
                            "notes": "Background check completed",
                            "generated_at": "2024-01-20T15:30:00Z"
                        }
                    ]
                }
            ),
            403: "Forbidden - Admin only"
        },
        tags=['Admin - Reports']
    )
    def get(self, request):
        """Get all reports for admin dashboard"""
        reports = Report.objects.all().order_by('-generated_at')
        serializer = AdminReportSerializer(reports, many=True)
        return Response(serializer.data)
