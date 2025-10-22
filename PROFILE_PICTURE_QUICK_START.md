# 📸 PROFILE PICTURE UPLOAD - READY TO TEST!

## ✅ Feature Successfully Added!

Profile picture upload has been added to the profile update API.

---

## 🎯 Quick Test in Postman (Step-by-Step)

### **STEP 1: Login**

**Request:**
```
POST http://127.0.0.1:8000/api/auth/login/
Content-Type: application/json

Body:
{
  "email": "anower.softvence@gmail.com",
  "password": "YOUR_ACTUAL_PASSWORD"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "...",
  "user": {...}
}
```

**→ Copy the `access` token!**

---

### **STEP 2: Upload Profile Picture**

**IMPORTANT:** Use `form-data`, NOT JSON!

1. **Create new request in Postman:**
   - Method: `PATCH`
   - URL: `http://127.0.0.1:8000/api/auth/profile/update/`

2. **Authorization tab:**
   - Type: `Bearer Token`
   - Token: `YOUR_ACCESS_TOKEN_FROM_STEP_1`

3. **Body tab:**
   - Select: `form-data` (NOT raw!)
   - Add row:
     - Key: `profile_picture`
     - Type: Change from "Text" to "File" (dropdown on right)
     - Value: Click "Select Files" and choose an image (JPG/PNG)

4. **Click Send**

**Success Response:**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "id": 1,
    "username": "anower77",
    "email": "anower.softvence@gmail.com",
    "full_name": "Anower",
    "phone_number": "+1234567890",
    "profile_picture": "/media/profile_pictures/user_xyz123.jpg",
    "profile_picture_url": "http://127.0.0.1:8000/media/profile_pictures/user_xyz123.jpg"
  }
}
```

---

### **STEP 3: Update Profile with Name AND Picture**

**Same setup as Step 2, but in Body (form-data):**

```
Key: full_name         | Type: Text | Value: Your Name
Key: phone_number      | Type: Text | Value: +1234567890
Key: profile_picture   | Type: File | Value: [SELECT IMAGE]
```

**Click Send**

---

### **STEP 4: View Profile**

```
GET http://127.0.0.1:8000/api/auth/profile/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "success": true,
  "user": {
    "profile_picture_url": "http://127.0.0.1:8000/media/profile_pictures/..."
  }
}
```

**You can open the `profile_picture_url` in your browser to see the image!**

---

## 📋 What Was Added

### **Database:**
- ✅ `profile_picture` field added to User model
- ✅ Migration created and applied
- ✅ Images stored in `/media/profile_pictures/`

### **API:**
- ✅ Profile picture upload via PATCH `/api/auth/profile/update/`
- ✅ Profile picture URL returned in GET `/api/auth/profile/`
- ✅ Supports multipart/form-data
- ✅ Can update picture alone or with other fields

### **Validations:**
- ✅ Max file size: 5MB
- ✅ Allowed formats: JPG, PNG, GIF, WEBP
- ✅ Old picture automatically deleted on update

---

## 🎬 Visual Guide for Postman

```
┌─────────────────────────────────────────────────────┐
│ Postman Request Setup                               │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Method: PATCH                                       │
│ URL: http://127.0.0.1:8000/api/auth/profile/update/│
│                                                     │
│ ┌─ Authorization Tab ──────────────────────────┐   │
│ │ Type: Bearer Token                           │   │
│ │ Token: [YOUR_ACCESS_TOKEN]                   │   │
│ └──────────────────────────────────────────────┘   │
│                                                     │
│ ┌─ Body Tab ───────────────────────────────────┐   │
│ │ Select: form-data (NOT raw!)                 │   │
│ │                                              │   │
│ │ ┌────────────────┬──────┬─────────────────┐ │   │
│ │ │ KEY            │ TYPE │ VALUE           │ │   │
│ │ ├────────────────┼──────┼─────────────────┤ │   │
│ │ │ profile_picture│ File │ [Select Files]  │ │   │
│ │ └────────────────┴──────┴─────────────────┘ │   │
│ │                                              │   │
│ │ To add more fields (optional):               │   │
│ │ ┌────────────────┬──────┬─────────────────┐ │   │
│ │ │ full_name      │ Text │ John Doe        │ │   │
│ │ │ phone_number   │ Text │ +1234567890     │ │   │
│ │ └────────────────┴──────┴─────────────────┘ │   │
│ └──────────────────────────────────────────────┘   │
│                                                     │
│ [Send] ←── Click here                              │
└─────────────────────────────────────────────────────┘
```

---

## ⚠️ Common Mistakes

### ❌ **Using JSON instead of form-data**
```
Body → raw → JSON  ❌ WRONG!
```

### ✅ **Correct: Use form-data**
```
Body → form-data → Add file  ✅ CORRECT!
```

---

### ❌ **Wrong Content-Type Header**
Don't manually set `Content-Type: application/json` when uploading files.

### ✅ **Correct: Let Postman handle it**
When you select "form-data", Postman automatically sets the correct `Content-Type: multipart/form-data` with boundary.

---

## 📊 API Response Examples

### **Before Upload (No Picture):**
```json
{
  "user": {
    "profile_picture": null,
    "profile_picture_url": null
  }
}
```

### **After Upload:**
```json
{
  "user": {
    "profile_picture": "/media/profile_pictures/profile_abc123.jpg",
    "profile_picture_url": "http://127.0.0.1:8000/media/profile_pictures/profile_abc123.jpg"
  }
}
```

---

## 🔍 Validation Errors

### **File Too Large:**
```json
{
  "profile_picture": ["Image file size must be less than 5MB"]
}
```
**Solution:** Use smaller image or compress it.

---

### **Invalid File Type:**
```json
{
  "profile_picture": ["Only JPG, PNG, GIF, and WEBP images are allowed"]
}
```
**Solution:** Convert to JPG or PNG.

---

### **No Authorization:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```
**Solution:** Add Bearer token in Authorization header.

---

## 🎯 Complete Test Flow

```
1. Login
   ↓
2. Get access token
   ↓
3. Set Bearer token in Postman
   ↓
4. Select form-data in Body
   ↓
5. Add profile_picture as File
   ↓
6. Select image from computer
   ↓
7. Send request
   ↓
8. Get profile_picture_url in response
   ↓
9. Open URL in browser to verify
```

---

## 📁 Files Created

1. ✅ **PROFILE_PICTURE_UPLOAD.md** - Complete documentation
2. ✅ **test_profile_picture.py** - Automated test script
3. ✅ **Migration:** `0004_user_profile_picture.py`

---

## 🚀 Ready to Test!

**Everything is configured and working.** Just:

1. Open Postman
2. Login to get token
3. Use **form-data** to upload image
4. See profile_picture_url in response

**The image will be saved in:** `/media/profile_pictures/`

---

## 📞 Need Help?

If you encounter issues:

1. ✅ Make sure you're using **form-data**, not JSON
2. ✅ Check Bearer token is set correctly
3. ✅ Image is JPG/PNG and under 5MB
4. ✅ Server is running: `python manage.py runserver`

---

**Status:** 🟢 **READY TO TEST IN POSTMAN!**
