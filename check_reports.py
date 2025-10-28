import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from background_requests.models import Request, Report

print("=== All Reports in Database ===")
reports = Report.objects.all().select_related('request')
print(f"Total reports: {reports.count()}\n")

for report in reports:
    print(f"Report ID: {report.id}")
    print(f"  Request ID: {report.request.id}")
    print(f"  Request Name: {report.request.name}")
    print(f"  Request Status: {report.request.status}")
    print(f"  Request User: {report.request.user.username}")
    print(f"  Verification Status: {report.verification_status}")
    print(f"  Has PDF: {bool(report.pdf)}")
    print(f"  Generated At: {report.generated_at}")
    print(f"  URL to test: http://127.0.0.1:8000/api/requests/api/{report.request.id}/view-report/")
    print()

print("\n=== All Completed Requests ===")
completed = Request.objects.filter(status='Completed')
print(f"Total completed: {completed.count()}\n")

for req in completed:
    print(f"Request ID: {req.id}, Name: {req.name}, User: {req.user.username}")
    print(f"  Has Report: {hasattr(req, 'report')}")
    if hasattr(req, 'report'):
        print(f"  Report ID: {req.report.id}")
    print()
