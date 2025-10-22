"""
Test Profile Picture Upload
Demonstrates how to upload and update profile pictures
"""

import os
import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from io import BytesIO
from PIL import Image

User = get_user_model()

def create_test_image():
    """Create a test image in memory"""
    # Create a simple 200x200 red image
    img = Image.new('RGB', (200, 200), color='red')
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    return SimpleUploadedFile(
        'test_profile.jpg',
        img_io.getvalue(),
        content_type='image/jpeg'
    )

def test_profile_picture_upload():
    """Test uploading profile picture"""
    print("=" * 70)
    print("📸 TESTING PROFILE PICTURE UPLOAD")
    print("=" * 70)
    
    client = APIClient()
    
    # Step 1: Login
    print("\n1️⃣ Logging in...")
    response = client.post('/api/auth/login/', {
        'email': 'anower.softvence@gmail.com',
        'password': 'Test123!'
    }, format='json')
    
    if response.status_code != 200:
        print("❌ Login failed! Make sure user exists with this password.")
        print(f"Response: {response.data}")
        return
    
    access_token = response.data['access']
    print(f"✅ Logged in successfully")
    print(f"User: {response.data['user']['username']}")
    
    # Set authorization header
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    
    # Step 2: Get current profile
    print("\n2️⃣ Getting current profile...")
    response = client.get('/api/auth/profile/')
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        user_data = response.data['user']
        print(f"✅ Current profile:")
        print(f"   Username: {user_data['username']}")
        print(f"   Email: {user_data['email']}")
        print(f"   Full Name: {user_data.get('full_name', 'Not set')}")
        print(f"   Profile Picture: {user_data.get('profile_picture_url', 'Not set')}")
    
    # Step 3: Upload profile picture
    print("\n3️⃣ Uploading profile picture...")
    
    # Create test image
    test_image = create_test_image()
    
    # Use multipart/form-data
    response = client.patch('/api/auth/profile/update/', {
        'profile_picture': test_image
    }, format='multipart')
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Profile picture uploaded successfully!")
        user_data = response.data['user']
        print(f"   Profile Picture URL: {user_data.get('profile_picture_url')}")
        print(f"   Profile Picture Path: {user_data.get('profile_picture')}")
    else:
        print(f"❌ Upload failed: {response.data}")
    
    # Step 4: Update profile with both name and picture
    print("\n4️⃣ Updating profile with name and picture...")
    
    test_image_2 = create_test_image()
    
    response = client.patch('/api/auth/profile/update/', {
        'full_name': 'Test User with Picture',
        'profile_picture': test_image_2
    }, format='multipart')
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ Profile updated successfully!")
        user_data = response.data['user']
        print(f"   Full Name: {user_data['full_name']}")
        print(f"   Profile Picture URL: {user_data.get('profile_picture_url')}")
    else:
        print(f"❌ Update failed: {response.data}")
    
    # Step 5: Get updated profile
    print("\n5️⃣ Getting updated profile...")
    response = client.get('/api/auth/profile/')
    
    if response.status_code == 200:
        user_data = response.data['user']
        print(f"✅ Updated profile:")
        print(f"   Username: {user_data['username']}")
        print(f"   Full Name: {user_data['full_name']}")
        print(f"   Profile Picture URL: {user_data.get('profile_picture_url')}")
        
        if user_data.get('profile_picture_url'):
            print(f"\n📷 Profile picture available at:")
            print(f"   {user_data['profile_picture_url']}")
    
    print("\n" + "=" * 70)
    print("✅ TEST COMPLETED!")
    print("=" * 70)

if __name__ == "__main__":
    test_profile_picture_upload()
