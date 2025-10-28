import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from background_requests.models import Request, Report

# Check requests
print("=== Background Check Requests ===")
requests = Request.objects.all()
print(f"Total requests: {requests.count()}\n")

for req in requests[:5]:
    print(f"ID: {req.id}")
    print(f"  Name: {req.name}")
    print(f"  Status: {req.status}")
    print(f"  User: {req.user.username}")
    print(f"  Has Report: {hasattr(req, 'report')}")
    if hasattr(req, 'report'):
        print(f"  Report ID: {req.report.id}")
        print(f"  Verification Status: {req.report.verification_status}")
    print()

# Try to access request 7
print("=== Testing Request ID 7 ===")
try:
    req7 = Request.objects.get(id=7)
    print(f"Request 7 found: {req7.name}, Status: {req7.status}")
    
    if hasattr(req7, 'report'):
        report = req7.report
        print(f"Report exists: ID {report.id}")
        print(f"Verification Status: {report.verification_status}")
        print(f"SSN Validation: {report.ssn_validation}")
        print(f"Address History: {report.address_history}")
    else:
        print("No report attached to this request")
        
except Request.DoesNotExist:
    print("Request 7 does not exist")
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
