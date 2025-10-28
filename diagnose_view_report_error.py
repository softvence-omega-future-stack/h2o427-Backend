import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from background_requests.models import Request, Report
from django.contrib.auth import get_user_model

User = get_user_model()

print("=== Testing view_report endpoint logic ===\n")

# Test with request ID 20 (has report)
request_id = 20

try:
    print(f"Testing Request ID: {request_id}")
    bg_request = Request.objects.get(id=request_id)
    print(f"✓ Request found: {bg_request.name}, Status: {bg_request.status}")
    
    # Check if report exists
    if hasattr(bg_request, 'report'):
        report = bg_request.report
        print(f"✓ Report found: ID {report.id}")
        
        # Try to access all the new fields
        print("\n--- Testing Report Fields ---")
        try:
            print(f"verification_status: {report.verification_status}")
        except Exception as e:
            print(f"✗ Error accessing verification_status: {e}")
        
        try:
            print(f"ssn_validation: {report.ssn_validation}")
        except Exception as e:
            print(f"✗ Error accessing ssn_validation: {e}")
            
        try:
            print(f"address_history: {report.address_history}")
        except Exception as e:
            print(f"✗ Error accessing address_history: {e}")
            
        try:
            print(f"identity_cross_reference: {report.identity_cross_reference}")
        except Exception as e:
            print(f"✗ Error accessing identity_cross_reference: {e}")
            
        try:
            print(f"database_match: {report.database_match}")
        except Exception as e:
            print(f"✗ Error accessing database_match: {e}")
            
        try:
            print(f"federal_criminal_records: {report.federal_criminal_records}")
        except Exception as e:
            print(f"✗ Error accessing federal_criminal_records: {e}")
            
        try:
            print(f"education_verified: {report.education_verified}")
        except Exception as e:
            print(f"✗ Error accessing education_verified: {e}")
            
        try:
            print(f"final_summary: {report.final_summary}")
        except Exception as e:
            print(f"✗ Error accessing final_summary: {e}")
            
    else:
        print("✗ No report attached")
        
except Request.DoesNotExist:
    print(f"✗ Request {request_id} not found")
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    traceback.print_exc()

print("\n=== Check all Report model fields ===")
from background_requests.models import Report
print("Report model fields:")
for field in Report._meta.get_fields():
    print(f"  - {field.name} ({type(field).__name__})")
