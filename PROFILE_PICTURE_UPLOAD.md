# 📸 Profile Picture Upload - API Documentation

## ✅ Feature Added: Profile Picture Upload

Users can now upload, update, and delete their profile pictures through the profile update API.

---

## 🔧 Changes Made

### **1. Database Model**
Added `profile_picture` field to User model:
```python
profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
```

### **2. API Serializers**
- `UserProfileSerializer`: Returns profile picture URL
- `UserProfileUpdateSerializer`: Handles image upload with validation

### **3. Validations**
- ✅ Max file size: 5MB
- ✅ Allowed formats: JPG, PNG, GIF, WEBP
- ✅ Automatic old picture deletion on update

---

## 📋 API Endpoints

### **1. Get Profile (with Picture URL)**

**Endpoint:** `GET /api/auth/profile/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "anower77",
    "email": "anower.softvence@gmail.com",
    "full_name": "Anower Hossain",
    "phone_number": "+1234567890",
    "profile_picture": "/media/profile_pictures/user_123.jpg",
    "profile_picture_url": "http://127.0.0.1:8000/media/profile_pictures/user_123.jpg",
    "date_joined": "2025-10-22T10:00:00Z",
    "last_login": "2025-10-22T12:00:00Z"
  }
}
```

---

### **2. Upload/Update Profile Picture**

**Endpoint:** `PATCH /api/auth/profile/update/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data
```

**Body (form-data):**
```
profile_picture: [FILE]
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "anower77",
    "email": "anower.softvence@gmail.com",
    "full_name": "Anower Hossain",
    "phone_number": "+1234567890",
    "profile_picture": "/media/profile_pictures/user_123_abc456.jpg",
    "profile_picture_url": "http://127.0.0.1:8000/media/profile_pictures/user_123_abc456.jpg",
    "date_joined": "2025-10-22T10:00:00Z",
    "last_login": "2025-10-22T12:00:00Z"
  }
}
```

---

### **3. Update Profile with Picture and Other Fields**

**Endpoint:** `PATCH /api/auth/profile/update/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data
```

**Body (form-data):**
```
full_name: John Doe
phone_number: +1234567890
profile_picture: [FILE]
```

**Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "anower77",
    "email": "anower.softvence@gmail.com",
    "full_name": "John Doe",
    "phone_number": "+1234567890",
    "profile_picture": "/media/profile_pictures/user_123_def789.jpg",
    "profile_picture_url": "http://127.0.0.1:8000/media/profile_pictures/user_123_def789.jpg",
    "date_joined": "2025-10-22T10:00:00Z",
    "last_login": "2025-10-22T12:00:00Z"
  }
}
```

---

## 🧪 Testing in Postman

### **Step 1: Get Access Token**

```
POST http://127.0.0.1:8000/api/auth/login/
Body (JSON):
{
  "email": "anower.softvence@gmail.com",
  "password": "Test123!"
}
```

**Save the `access` token from response.**

---

### **Step 2: Upload Profile Picture**

1. **Create new request:**
   - Method: `PATCH`
   - URL: `http://127.0.0.1:8000/api/auth/profile/update/`

2. **Set Authorization:**
   - Type: Bearer Token
   - Token: `YOUR_ACCESS_TOKEN`

3. **Set Body:**
   - Type: `form-data` (NOT raw JSON!)
   - Add key: `profile_picture`
   - Type: `File`
   - Value: Select image file from your computer

4. **Send Request**

**Success Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "profile_picture_url": "http://127.0.0.1:8000/media/profile_pictures/..."
  }
}
```

---

### **Step 3: Update Profile with Name AND Picture**

1. **Same URL and Authorization as Step 2**

2. **Body (form-data):**
   ```
   Key: full_name         | Value: John Doe
   Key: phone_number      | Value: +1234567890
   Key: profile_picture   | Type: File | Value: [SELECT IMAGE]
   ```

3. **Send Request**

---

### **Step 4: Get Updated Profile**

```
GET http://127.0.0.1:8000/api/auth/profile/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response includes profile_picture_url:**
```json
{
  "user": {
    "profile_picture_url": "http://127.0.0.1:8000/media/profile_pictures/..."
  }
}
```

---

## 🎯 Postman Collection (Import This)

```json
{
  "name": "Profile Picture Upload",
  "item": [
    {
      "name": "1. Login",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"email\": \"anower.softvence@gmail.com\",\n  \"password\": \"Test123!\"\n}"
        },
        "url": {
          "raw": "{{base_url}}/api/auth/login/",
          "host": ["{{base_url}}"],
          "path": ["api", "auth", "login", ""]
        }
      }
    },
    {
      "name": "2. Get Profile",
      "request": {
        "method": "GET",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ],
        "url": {
          "raw": "{{base_url}}/api/auth/profile/",
          "host": ["{{base_url}}"],
          "path": ["api", "auth", "profile", ""]
        }
      }
    },
    {
      "name": "3. Upload Profile Picture",
      "request": {
        "method": "PATCH",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "profile_picture",
              "type": "file",
              "src": "/path/to/your/image.jpg"
            }
          ]
        },
        "url": {
          "raw": "{{base_url}}/api/auth/profile/update/",
          "host": ["{{base_url}}"],
          "path": ["api", "auth", "profile", "update", ""]
        }
      }
    },
    {
      "name": "4. Update Profile with Picture",
      "request": {
        "method": "PATCH",
        "header": [
          {
            "key": "Authorization",
            "value": "Bearer {{access_token}}"
          }
        ],
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "full_name",
              "value": "John Doe",
              "type": "text"
            },
            {
              "key": "phone_number",
              "value": "+1234567890",
              "type": "text"
            },
            {
              "key": "profile_picture",
              "type": "file",
              "src": "/path/to/your/image.jpg"
            }
          ]
        },
        "url": {
          "raw": "{{base_url}}/api/auth/profile/update/",
          "host": ["{{base_url}}"],
          "path": ["api", "auth", "profile", "update", ""]
        }
      }
    }
  ]
}
```

---

## 📝 Important Notes

### **Content-Type:**
- ⚠️ **Must use `multipart/form-data`** when uploading files
- ⚠️ **NOT `application/json`** when including file
- In Postman: Select "form-data" in Body tab

### **File Validations:**
- **Max Size:** 5MB
- **Allowed Formats:** JPG, JPEG, PNG, GIF, WEBP
- **Upload Location:** `/media/profile_pictures/`

### **Old Picture Handling:**
- ✅ Old picture is automatically deleted when new one is uploaded
- ✅ Prevents storage bloat
- ✅ No manual cleanup needed

### **Response Fields:**
- `profile_picture`: Relative path (e.g., `/media/profile_pictures/image.jpg`)
- `profile_picture_url`: Full URL (e.g., `http://127.0.0.1:8000/media/profile_pictures/image.jpg`)

---

## 🐛 Error Responses

### **File Too Large**
```json
{
  "profile_picture": ["Image file size must be less than 5MB"]
}
```

### **Invalid File Type**
```json
{
  "profile_picture": ["Only JPG, PNG, GIF, and WEBP images are allowed"]
}
```

### **No File Uploaded**
```json
{
  "profile_picture": ["No file was submitted."]
}
```

### **Unauthorized**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ 1. User Logs In                                         │
│    POST /api/auth/login/                                │
│    → Receives access token                              │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 2. User Uploads Profile Picture                        │
│    PATCH /api/auth/profile/update/                      │
│    Content-Type: multipart/form-data                    │
│    Body: profile_picture=[FILE]                         │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Server Validates Image                               │
│    - Check file size (max 5MB)                          │
│    - Check file type (JPG/PNG/GIF/WEBP)                 │
│    - Delete old picture if exists                       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 4. Server Saves Image                                   │
│    - Upload to /media/profile_pictures/                 │
│    - Generate unique filename                           │
│    - Update user record                                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ 5. Return Updated Profile                               │
│    - profile_picture: relative path                     │
│    - profile_picture_url: full URL                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🧪 Test Script

Run automated test:

```bash
python test_profile_picture.py
```

This script will:
1. ✅ Login user
2. ✅ Get current profile
3. ✅ Upload profile picture
4. ✅ Update profile with name and picture
5. ✅ Verify profile picture URL

---

## ✅ Testing Checklist

- [ ] Login successful (get access token)
- [ ] Can upload profile picture (PATCH with form-data)
- [ ] Profile picture URL returned in response
- [ ] Old picture deleted when uploading new one
- [ ] File size validation working (reject >5MB)
- [ ] File type validation working (reject non-images)
- [ ] Can update name and picture together
- [ ] Profile picture accessible via URL
- [ ] GET profile returns picture URL

---

## 🎯 Quick Test Commands

### **Using cURL (Windows PowerShell):**

**1. Login:**
```powershell
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" -Method POST -Body (@{email="anower.softvence@gmail.com";password="Test123!"} | ConvertTo-Json) -ContentType "application/json"
$token = $response.access
```

**2. Upload Picture:**
```powershell
$headers = @{Authorization="Bearer $token"}
$filePath = "C:\path\to\your\image.jpg"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/profile/update/" -Method PATCH -Headers $headers -Form @{profile_picture=Get-Item $filePath}
```

---

**Status:** 🟢 Profile Picture Upload Fully Working!

**Test Now:**
1. Open Postman
2. Login to get token
3. Use form-data (NOT JSON) to upload image
4. Check response for profile_picture_url
