"""
Simple script to upload a PDF report to production using the admin endpoint
"""
import requests
import os

BASE_URL = "http://127.0.0.1:8000/"
UPLOAD_ENDPOINT = f"{BASE_URL}/api/admin/reports/upload/"

print("=" * 70)
print("ADMIN REPORT UPLOAD TO CLOUDINARY")
print("=" * 70)

# Get admin token
admin_token = input("\nEnter your ADMIN Bearer token: ").strip()

if not admin_token:
    print("Token is required!")
    exit(1)

# Get request ID
request_id = input("Enter Request ID (e.g., 6): ").strip()

if not request_id:
    print("Request ID is required!")
    exit(1)

# Get PDF file path
pdf_path = input("Enter path to PDF file: ").strip().strip('"')

if not os.path.exists(pdf_path):
    print(f"File not found: {pdf_path}")
    exit(1)

# Optional notes
notes = input("Enter notes (optional, press Enter to skip): ").strip()

print("\n" + "=" * 70)
print("UPLOADING...")
print("=" * 70)

# Prepare the request
headers = {
    "Authorization": f"Bearer {admin_token}"
}

# IMPORTANT: The field name must be 'pdf', not 'report_file'
files = {
    'pdf': open(pdf_path, 'rb')
}

data = {
    'request_id': request_id,
}

if notes:
    data['notes'] = notes

try:
    response = requests.post(
        UPLOAD_ENDPOINT,
        headers=headers,
        files=files,
        data=data,
        timeout=30
    )
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n SUCCESS!")
        print("\nResponse:")
        print(f"  Message: {result.get('message')}")
        
        report = result.get('report', {})
        print(f"\n  Report ID: {report.get('id')}")
        print(f"  PDF URL: {report.get('pdf')}")
        print(f"  Notes: {report.get('notes')}")
        print(f"  Generated At: {report.get('generated_at')}")
        
        # Check if Cloudinary is being used
        pdf_url = report.get('pdf', '')
        if 'cloudinary' in pdf_url.lower():
            print("\n File uploaded to CLOUDINARY!")
            print("   The file will persist permanently.")
        else:
            print("\n  File uploaded to LOCAL storage (ephemeral)")
            print("   You need to set DEBUG=False in Render environment!")
            print("\n   Steps:")
            print("   1. Go to: https://dashboard.render.com")
            print("   2. Select: h2o427-backend")
            print("   3. Environment tab → Add: DEBUG=False")
            print("   4. Save and wait for redeploy")
            print("   5. Upload again - it will go to Cloudinary")
        
    else:
        print("\n UPLOAD FAILED")
        print(f"\nError Response:")
        try:
            print(response.json())
        except:
            print(response.text)
            
except requests.exceptions.RequestException as e:
    print(f"\n Request Error: {e}")
except Exception as e:
    print(f"\n Error: {e}")
finally:
    files['pdf'].close()

print("\n" + "=" * 70)
