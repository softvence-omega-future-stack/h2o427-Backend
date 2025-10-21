# Authentication Fix Summary

## Issue
The authentication endpoints (registration and login) were failing with:
```
ProgrammingError: column authentication_user.confirm_password does not exist
```

## Root Cause
The User model incorrectly defined `password` and `confirm_password` as database fields. These should NOT be database columns because:
1. `password` is already handled by Django's `AbstractUser` (as a hashed field)
2. `confirm_password` should only exist in the serializer for validation, never in the database

## Fixes Applied

### 1. Updated User Model (`authentication/models.py`)
**Before:**
```python
class User(AbstractUser):
    full_name = models.CharField(...)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(...)
    password = models.CharField(max_length=255)  # ❌ Wrong!
    confirm_password = models.CharField(max_length=255)  # ❌ Wrong!
```

**After:**
```python
class User(AbstractUser):
    full_name = models.CharField(...)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(...)
    # password is inherited from AbstractUser ✅
    # confirm_password removed ✅
    REQUIRED_FIELDS = ['email']
```

### 2. Updated Serializer (`authentication/serializers.py`)
- Made `password` and `confirm_password` write-only fields
- Added proper password hashing using `create_user()` method
- Remove `confirm_password` before creating the user object
- Added `username` field (uses email if not provided)

**Key changes:**
```python
def create(self, validated_data):
    validated_data.pop('confirm_password', None)  # Remove validation-only field
    
    user = User.objects.create_user(  # Use create_user for proper password hashing
        username=validated_data.get('username', validated_data['email']),
        email=validated_data['email'],
        password=validated_data['password'],
        ...
    )
    return user
```

### 3. Added Email Authentication Backend
Created `authentication/backends.py` to allow login with email instead of username:

```python
class EmailBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Allows login with email OR username
```

Added to `settings.py`:
```python
AUTHENTICATION_BACKENDS = [
    'authentication.backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
]
```

### 4. Updated Views
- Added `permission_classes = []` to allow unauthenticated access to registration/login
- Added GET methods for browsable API documentation
- Added better error handling for OTP (Twilio) failures
- Improved response data with user information

### 5. Migration Handling
- Created migration to remove invalid fields
- Faked the migration since columns never existed in database

## Testing

### Manual Testing
1. Start the server:
   ```bash
   python manage.py runserver
   ```

2. Test Registration:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/auth/register/ \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "test@example.com",
       "password": "TestPass123!",
       "confirm_password": "TestPass123!",
       "full_name": "Test User"
     }'
   ```

3. Test Login:
   ```bash
   curl -X POST http://127.0.0.1:8000/api/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "TestPass123!"
     }'
   ```

### Automated Testing
Run the test script:
```bash
python test_auth.py
```

## API Endpoints

### Registration: `POST /api/auth/register/`
**Request:**
```json
{
  "username": "testuser",  // optional, will use email if not provided
  "full_name": "Test User",
  "email": "test@example.com",
  "phone_number": "+1234567890",  // optional
  "password": "TestPassword123!",
  "confirm_password": "TestPassword123!"
}
```

**Response (201 Created):**
```json
{
  "message": "User registered successfully!",
  "user": {
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User"
  }
}
```

### Login: `POST /api/auth/login/`
**Request:**
```json
{
  "email": "test@example.com",  // or username
  "password": "TestPassword123!"
}
```

**Response (200 OK):**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "username": "testuser",
    "full_name": "Test User",
    "email": "test@example.com",
    "phone_number": "+1234567890"
  }
}
```

## Files Modified

1. ✅ `authentication/models.py` - Removed invalid password fields
2. ✅ `authentication/serializers.py` - Fixed user creation logic
3. ✅ `authentication/views.py` - Added GET methods and better responses
4. ✅ `authentication/backends.py` - Created email authentication backend
5. ✅ `background_check/settings.py` - Added authentication backend
6. ✅ `authentication/migrations/0002_*.py` - Created and faked migration

## Verification

Run these commands to verify everything works:

```bash
# Check for issues
python manage.py check

# Verify migrations
python manage.py showmigrations

# Start server
python manage.py runserver

# Test endpoints (in browser or with curl)
# Visit: http://127.0.0.1:8000/api/auth/register/
# Visit: http://127.0.0.1:8000/api/auth/login/
```

## Status
✅ **All authentication issues fixed!**
- ✅ Registration endpoint working
- ✅ Login endpoint working
- ✅ Email-based authentication enabled
- ✅ Password hashing working correctly
- ✅ JWT token generation working
- ✅ Browsable API forms available
