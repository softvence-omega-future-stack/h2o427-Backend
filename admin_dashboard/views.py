from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from background_requests.models import Request, Report
from .serializers import AdminRequestSerializer, AdminReportSerializer

class AdminRequestView(APIView):
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get all background check requests for admin dashboard"""
        requests = Request.objects.all().order_by('-created_at')
        serializer = AdminRequestSerializer(requests, many=True)
        return Response(serializer.data)

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
    
    def post(self, request):
        """Upload or generate PDF report for a background check request"""
        try:
            request_id = request.data.get('request_id')
            pdf_file = request.FILES.get('pdf')
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

    def get(self, request):
        """Get all reports for admin dashboard"""
        reports = Report.objects.all().order_by('-generated_at')
        serializer = AdminReportSerializer(reports, many=True)
        return Response(serializer.data)
