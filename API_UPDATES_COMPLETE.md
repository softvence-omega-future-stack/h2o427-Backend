# API Updates - Completion Summary

## ✅ All 5 Requested Updates Implemented

### 1. ✅ Logout API
**Endpoint:** `POST /api/auth/logout/`

**Implementation:**
- Added `UserLogoutView` in `authentication/views.py`
- Configured JWT token blacklisting in `background_check/settings.py`
- Added `rest_framework_simplejwt.token_blacklist` to `INSTALLED_APPS`
- Applied all token_blacklist migrations (12 migrations)

**Request Body:**
```json
{
  "refresh": "your_refresh_token_here"
}
```

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

**Usage:**
- Send POST request with refresh token
- Token will be blacklisted and cannot be reused
- Returns 205 status code on success

---

### 2. ✅ Password Reset URL with Domain Configuration
**Updated Files:**
- `authentication/serializers.py` - ForgotPasswordSerializer

**Implementation:**
- Password reset emails now use environment variables for URLs
- Frontend URL: Uses `FRONTEND_URL` environment variable (default: http://localhost:3000)
- Backend URL: Uses `RENDER_EXTERNAL_HOSTNAME` environment variable (default: http://127.0.0.1:8000)

**Environment Variables to Set:**
```env
FRONTEND_URL=http://localhost:3000  # For local development
# or
FRONTEND_URL=https://your-frontend-domain.com  # For production

RENDER_EXTERNAL_HOSTNAME=https://h2o427-backend-u9bx.onrender.com  # For production
# or
RENDER_EXTERNAL_HOSTNAME=http://127.0.0.1:8000  # For local development
```

**Email Template:**
- Reset link: `{FRONTEND_URL}/reset-password/{uid}/{token}/`
- Verification link: `{RENDER_EXTERNAL_HOSTNAME}/api/auth/reset-password/{uid}/{token}/`

---

### 3. ✅ Removed SSN, Address, Zip Code from Background Check Request API
**Endpoint:** `POST /api/requests/api/`

**Changes Made:**
- Updated Swagger documentation in `background_requests/views.py`
- Removed `ssn`, `address`, `zip_code` from required fields
- Updated request schema to match actual model fields

**Current Required Fields:**
```json
{
  "name": "John Smith",
  "dob": "1990-05-15",
  "city": "New York",
  "state": "NY",
  "email": "john.smith@example.com",
  "phone_number": "+1234567890"
}
```

**Removed Fields:**
- ❌ ssn (Social Security Number)
- ❌ address (Street address)
- ❌ zip_code (ZIP code)

**Note:** Database model and serializers were already clean - only Swagger documentation was updated.

---

### 4. ✅ User Profile Picture Upload with Edit Option
**Endpoints:**
- **View Profile:** `GET /api/auth/profile/`
- **Upload/Update Profile Picture:** `PATCH /api/auth/profile/update/`

**Implementation:**
- Model field: `profile_picture` in `authentication/models.py`
- Migration: `0004_user_profile_picture.py` (already applied)
- Serializer: `UserProfileUpdateSerializer` in `authentication/serializers.py`

**Upload Profile Picture:**
```http
PATCH /api/auth/profile/update/
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

profile_picture: [FILE]
```

**Supported Formats:**
- JPG, JPEG, PNG, GIF, WEBP
- Maximum size: 5MB

**Features:**
- Automatic deletion of old profile picture when uploading new one
- Returns full profile picture URL in response
- Validation for file format and size

**Response Example:**
```json
{
  "id": 1,
  "username": "john_smith",
  "email": "john@example.com",
  "full_name": "John Smith",
  "phone_number": "+1234567890",
  "profile_picture": "/media/profile_pictures/john.jpg",
  "profile_picture_url": "http://localhost:8000/media/profile_pictures/john.jpg"
}
```

---

### 5. ✅ Edit User Profile Fields
**Endpoint:** `PATCH /api/auth/profile/update/`

**Implementation:**
- View: `UserProfileUpdateView` in `authentication/views.py`
- Serializer: `UserProfileUpdateSerializer` in `authentication/serializers.py`
- Supports partial updates (PATCH)

**Editable Fields:**
```json
{
  "full_name": "John Smith",
  "phone_number": "+1234567890",
  "profile_picture": [FILE]
}
```

**Example Request:**
```http
PATCH /api/auth/profile/update/
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "full_name": "John Doe",
  "phone_number": "+9876543210"
}
```

**Example Request (with file):**
```http
PATCH /api/auth/profile/update/
Content-Type: multipart/form-data
Authorization: Bearer <access_token>

full_name: John Doe
phone_number: +9876543210
profile_picture: [FILE]
```

**Response:**
```json
{
  "id": 1,
  "username": "john_smith",
  "email": "john@example.com",
  "full_name": "John Doe",
  "phone_number": "+9876543210",
  "profile_picture": "/media/profile_pictures/new_pic.jpg",
  "profile_picture_url": "http://localhost:8000/media/profile_pictures/new_pic.jpg",
  "date_joined": "2024-01-15T10:00:00Z",
  "last_login": "2024-01-20T14:30:00Z"
}
```

**Read-Only Fields:**
- `id`, `username`, `email`, `date_joined`, `last_login`

---

## 🔧 Testing Instructions

### Test Logout API:
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your_refresh_token"}'
```

### Test Password Reset:
1. Request password reset: `POST /api/auth/forgot-password/`
2. Check email for reset link with correct domain
3. Verify link format: `{FRONTEND_URL}/reset-password/{uid}/{token}/`

### Test Background Check Request (without SSN/address/zip):
```bash
curl -X POST http://localhost:8000/api/requests/api/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "dob": "1990-05-15",
    "city": "New York",
    "state": "NY",
    "email": "john@example.com",
    "phone_number": "+1234567890"
  }'
```

### Test Profile Picture Upload:
```bash
curl -X PATCH http://localhost:8000/api/auth/profile/update/ \
  -H "Authorization: Bearer <token>" \
  -F "profile_picture=@/path/to/image.jpg"
```

### Test Profile Edit:
```bash
curl -X PATCH http://localhost:8000/api/auth/profile/update/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "phone_number": "+9876543210"
  }'
```

---

## 📋 API Documentation

All endpoints are documented in Swagger:
- **Swagger UI:** http://localhost:8000/swagger/
- **ReDoc:** http://localhost:8000/redoc/

Each endpoint includes:
- Request/response examples
- Required/optional fields
- Authentication requirements
- Status codes

---

## ✅ Database Migrations Status

All migrations applied successfully:
- ✅ Token blacklist tables created (12 migrations)
- ✅ Profile picture field exists
- ✅ All authentication tables up to date
- ✅ All background_requests tables up to date

---

## 🎉 Summary

All 5 requested updates have been successfully implemented:

1. ✅ **Logout API** - JWT token blacklisting configured and working
2. ✅ **Password Reset URLs** - Environment variables for frontend/backend domains
3. ✅ **Removed SSN/address/zip** - Swagger documentation updated
4. ✅ **Profile Picture Upload** - Full upload/edit functionality with 5MB limit
5. ✅ **Profile Edit** - PATCH endpoint for updating user profile fields

**No additional migrations needed** - all database changes are complete.

**Ready for testing!** 🚀
