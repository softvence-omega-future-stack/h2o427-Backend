import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from background_requests.models import Request, Report
from django.contrib.auth import get_user_model

User = get_user_model()

print("=" * 60)
print("ENDPOINT TESTING GUIDE")
print("=" * 60)

# Find admin user
admin = User.objects.filter(is_staff=True).first()
if admin:
    print(f"\nAdmin User: {admin.username}")
    print("Login to get admin token:")
    print(f'POST /api/authentication/login/')
    print(f'{{"username": "{admin.username}", "password": "your_password"}}')
else:
    print("\nNo admin user found. Create one first.")

# Find requests without reports
pending = Request.objects.filter(status__in=['Pending', 'In Progress']).exclude(report__isnull=False)
print(f"\n\nRequests Needing Reports: {pending.count()}")
print("-" * 60)

for req in pending[:5]:
    print(f"\nRequest ID: {req.id}")
    print(f"  Name: {req.name}")
    print(f"  Email: {req.email}")
    print(f"  Status: {req.status}")
    print(f"  User: {req.user.username}")
    print(f"  Created: {req.created_at.strftime('%Y-%m-%d')}")
    print(f"\n  Test URLs:")
    print(f"  GET  /api/requests/api/{req.id}/admin-report-form/")
    print(f"  POST /api/requests/api/{req.id}/submit-report/")

# Find completed reports
completed = Request.objects.filter(status='Completed', report__isnull=False)
print(f"\n\nCompleted Reports: {completed.count()}")
print("-" * 60)

for req in completed[:3]:
    print(f"\nRequest ID: {req.id}")
    print(f"  Name: {req.name}")
    print(f"  Status: {req.status}")
    print(f"  User: {req.user.username}")
    print(f"\n  Client View URL:")
    print(f"  GET /api/requests/api/{req.id}/view-report/")

print("\n" + "=" * 60)
print("QUICK TEST COMMANDS")
print("=" * 60)

if pending.exists():
    first_pending = pending.first()
    print(f"\n1. Get pending reports list:")
    print(f"   GET http://127.0.0.1:8000/api/requests/api/pending-reports/")
    
    print(f"\n2. Get form for request {first_pending.id}:")
    print(f"   GET http://127.0.0.1:8000/api/requests/api/{first_pending.id}/admin-report-form/")
    
    print(f"\n3. Submit report for request {first_pending.id}:")
    print(f"   POST http://127.0.0.1:8000/api/requests/api/{first_pending.id}/submit-report/")
    print(f"   Body:")
    print('''   {
     "ssn_validation": "Verified",
     "address_history": "Clear",
     "identity_cross_reference": "Clear",
     "database_match": "Verified",
     "verification_status": "clear"
   }''')

if completed.exists():
    first_completed = completed.first()
    print(f"\n4. View completed report {first_completed.id}:")
    print(f"   GET http://127.0.0.1:8000/api/requests/api/{first_completed.id}/view-report/")

print("\n\nSwagger UI: http://127.0.0.1:8000/swagger/")
print("=" * 60)
