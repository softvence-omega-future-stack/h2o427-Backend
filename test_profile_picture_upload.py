"""
Test script to verify profile picture upload functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'background_check.settings')
django.setup()

from authentication.models import User
from authentication.serializers import UserProfileUpdateSerializer, UserProfileSerializer
from django.core.files.uploadedfile import SimpleUploadedFile
from io import BytesIO
from PIL import Image

def create_test_image():
    """Create a test image in memory"""
    # Create a simple red 100x100 image
    img = Image.new('RGB', (100, 100), color='red')
    img_io = BytesIO()
    img.save(img_io, format='JPEG')
    img_io.seek(0)
    
    return SimpleUploadedFile(
        name='test_profile.jpg',
        content=img_io.read(),
        content_type='image/jpeg'
    )

def test_profile_picture_upload():
    """Test profile picture upload"""
    print("=" * 60)
    print("PROFILE PICTURE UPLOAD TEST")
    print("=" * 60)
    
    # Get a user (use first user or create one)
    try:
        user = User.objects.first()
        if not user:
            print("❌ No users found in database. Please create a user first.")
            return False
        
        print(f"✓ Testing with user: {user.username} (ID: {user.id})")
        print(f"✓ Current profile picture: {user.profile_picture or 'None'}")
        
        # Create test image
        test_image = create_test_image()
        print(f"✓ Created test image: {test_image.name} ({test_image.size} bytes)")
        
        # Update profile with image
        data = {
            'profile_picture': test_image,
            'full_name': user.full_name or 'Test User'
        }
        
        serializer = UserProfileUpdateSerializer(
            user,
            data=data,
            partial=True
        )
        
        if serializer.is_valid():
            updated_user = serializer.save()
            print(f"✅ Profile picture uploaded successfully!")
            print(f"✓ New profile picture path: {updated_user.profile_picture}")
            print(f"✓ File exists: {updated_user.profile_picture.storage.exists(updated_user.profile_picture.name)}")
            
            # Get profile data with URL
            profile_serializer = UserProfileSerializer(updated_user)
            profile_data = profile_serializer.data
            
            print(f"✓ Profile picture URL: {profile_data.get('profile_picture_url', 'N/A')}")
            print("\n" + "=" * 60)
            print("PROFILE DATA:")
            print("=" * 60)
            for key, value in profile_data.items():
                print(f"{key}: {value}")
            
            return True
        else:
            print(f"❌ Validation errors: {serializer.errors}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_media_settings():
    """Check media configuration"""
    print("\n" + "=" * 60)
    print("MEDIA CONFIGURATION CHECK")
    print("=" * 60)
    
    from django.conf import settings
    
    print(f"MEDIA_URL: {settings.MEDIA_URL}")
    print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
    print(f"MEDIA_ROOT exists: {os.path.exists(settings.MEDIA_ROOT)}")
    
    profile_pictures_dir = os.path.join(settings.MEDIA_ROOT, 'profile_pictures')
    print(f"Profile pictures dir: {profile_pictures_dir}")
    print(f"Profile pictures dir exists: {os.path.exists(profile_pictures_dir)}")
    
    if not os.path.exists(profile_pictures_dir):
        os.makedirs(profile_pictures_dir, exist_ok=True)
        print(f"✓ Created profile_pictures directory")

def check_pillow():
    """Check if Pillow is installed"""
    print("\n" + "=" * 60)
    print("PILLOW CHECK")
    print("=" * 60)
    try:
        from PIL import Image
        print(f"✅ Pillow is installed: {Image.__version__ if hasattr(Image, '__version__') else 'version unknown'}")
        return True
    except ImportError:
        print("❌ Pillow is NOT installed. Run: pip install Pillow")
        return False

if __name__ == "__main__":
    print("\n🔍 Starting Profile Picture Upload Tests...\n")
    
    # Check Pillow
    if not check_pillow():
        sys.exit(1)
    
    # Check media settings
    check_media_settings()
    
    # Test upload
    if test_profile_picture_upload():
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Tests failed!")
        sys.exit(1)
