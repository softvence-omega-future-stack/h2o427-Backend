# Complete Notification Testing Guide

## Overview

This guide will test the complete notification system step-by-step using Postman.

## What Gets Tested

1. User submits background check request → Admin receives notification
2. Admin updates request status → User receives notification
3. Admin submits report → User receives notification
4. Push notifications sent to FCM devices

## Prerequisites

1. Postman installed
2. Two test accounts:
   - Regular user account (for submitting requests)
   - Admin account (for approving and managing requests)

## Setup: Create Test Accounts

### Create Regular User Account

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/auth/register/
Content-Type: application/json
```

**Body:**
```json
{
  "username": "testuser",
  "email": "testuser@example.com",
  "password": "TestPass123!",
  "full_name": "Test User"
}
```

### Create Admin Account (If Needed)

Use Django admin or shell:
```python
python manage.py createsuperuser
```

Or promote existing user to admin:
```python
python manage.py shell
from authentication.models import User
user = User.objects.get(email='admin@example.com')
user.is_staff = True
user.is_superuser = True
user.save()
```

## Test Flow

### STEP 1: Login as Regular User

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/auth/login/
Content-Type: application/json
```

**Body:**
```json
{
  "email": "testuser@example.com",
  "password": "TestPass123!"
}
```

**Save Response:**
Copy the `access` token - this is your USER_TOKEN

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",  // COPY THIS
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### STEP 2: Register User's Device for Notifications

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/notifications/fcm-devices/
Authorization: Bearer USER_TOKEN
Content-Type: application/json
```

**Body:**
```json
{
  "registration_token": "cvF30bCQQOWhd3ZDzdikrl:APA91bFTeDckJySEQ989h7r2Fb8WCFl8j2LejX8MEUjYuVJv0xsX-UIhhmjCCV0q3yaxL9ZaWJ7YiePLVGOHZW1QageWJaZnVIx0-MvPS2q_2xzWMyaCbsI",
  "device_type": "web"
}
```

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "registration_token": "cvF30bCQQOWhd3ZDzdikrl...",
  "device_type": "web",
  "active": true,
  "created_at": "2025-11-06T10:00:00Z",
  "updated_at": "2025-11-06T10:00:00Z"
}
```

### STEP 3: Submit Background Check Request (User)

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/requests/api/
Authorization: Bearer USER_TOKEN
Content-Type: application/json
```

**Body:**
```json
{
  "name": "John Smith",
  "dob": "1990-05-15",
  "city": "New York",
  "state": "NY",
  "email": "john.smith@example.com",
  "phone_number": "+12125551234"
}
```

**Expected Response (201 Created):**
```json
{
  "id": 1,
  "user": 1,
  "name": "John Smith",
  "dob": "1990-05-15",
  "city": "New York",
  "state": "NY",
  "email": "john.smith@example.com",
  "phone_number": "+12125551234",
  "status": "Pending",
  "created_at": "2025-11-06T10:05:00Z",
  "updated_at": "2025-11-06T10:05:00Z"
}
```

**What Happens Automatically:**
- System creates notification for all admins
- System creates confirmation notification for user
- Push notifications sent to registered devices

### STEP 4: Check User Notifications

**Request:**
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/
Authorization: Bearer USER_TOKEN
```

**Expected Response (200 OK):**
```json
[
  {
    "id": 2,
    "recipient": 1,
    "recipient_details": {
      "id": 1,
      "username": "testuser",
      "email": "testuser@example.com",
      "full_name": "Test User"
    },
    "sender": null,
    "sender_details": null,
    "type": "system",
    "type_display": "System",
    "category": "background_check",
    "category_display": "Background Check",
    "title": "Background Check Request Received",
    "message": "Your background check request for John Smith has been received and is being processed.",
    "is_read": false,
    "read_at": null,
    "related_object_type": "Request",
    "related_object_id": 1,
    "action_url": null,
    "created_at": "2025-11-06T10:05:01Z",
    "updated_at": "2025-11-06T10:05:01Z"
  }
]
```

**VERIFY:** You should see 1 notification confirming request received.

### STEP 5: Login as Admin

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/auth/login/
Content-Type: application/json
```

**Body:**
```json
{
  "email": "admin@example.com",
  "password": "AdminPass123!"
}
```

**Save Response:**
Copy the `access` token - this is your ADMIN_TOKEN

### STEP 6: Register Admin's Device

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/notifications/fcm-devices/
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json
```

**Body:**
```json
{
  "registration_token": "admin_fcm_token_here_different_from_user",
  "device_type": "web"
}
```

### STEP 7: Check Admin Notifications

**Request:**
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/
Authorization: Bearer ADMIN_TOKEN
```

**Expected Response (200 OK):**
```json
[
  {
    "id": 1,
    "recipient": 2,
    "recipient_details": {
      "id": 2,
      "username": "admin",
      "email": "admin@example.com",
      "full_name": "Admin User"
    },
    "sender": 1,
    "sender_details": {
      "id": 1,
      "username": "testuser",
      "email": "testuser@example.com",
      "full_name": "Test User"
    },
    "type": "user_to_admin",
    "type_display": "User To Admin",
    "category": "background_check",
    "category_display": "Background Check",
    "title": "New Background Check Request",
    "message": "testuser has submitted a new background check request for John Smith.",
    "is_read": false,
    "read_at": null,
    "related_object_type": "Request",
    "related_object_id": 1,
    "action_url": "/admin/background_requests/request/1/change/",
    "created_at": "2025-11-06T10:05:00Z",
    "updated_at": "2025-11-06T10:05:00Z"
  }
]
```

**VERIFY:** Admin should see notification about new request from user.

### STEP 8: Admin Updates Request Status

**Request:**
```
PUT https://h2o427-backend-u9bx.onrender.com/api/requests/api/1/
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json
```

**Body:**
```json
{
  "status": "In Progress"
}
```

**Expected Response (200 OK):**
```json
{
  "id": 1,
  "status": "In Progress",
  ...
}
```

**What Happens Automatically:**
- System detects status change
- System creates notification for user
- Push notification sent to user's device

### STEP 9: User Checks for Status Update Notification

**Request:**
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/?is_read=false
Authorization: Bearer USER_TOKEN
```

**Expected Response (200 OK):**
```json
[
  {
    "id": 3,
    "title": "Background Check Status: In Progress",
    "message": "Your background check is now in progress.",
    "type": "admin_to_user",
    "category": "background_check",
    "is_read": false,
    "created_at": "2025-11-06T10:10:00Z"
  },
  {
    "id": 2,
    "title": "Background Check Request Received",
    "message": "Your background check request for John Smith has been received and is being processed.",
    "type": "system",
    "category": "background_check",
    "is_read": false,
    "created_at": "2025-11-06T10:05:01Z"
  }
]
```

**VERIFY:** User should see notification about status change to "In Progress".

### STEP 10: Admin Completes Request and Submits Report

**Request:**
```
PUT https://h2o427-backend-u9bx.onrender.com/api/requests/api/1/
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json
```

**Body:**
```json
{
  "status": "Completed"
}
```

**What Happens Automatically:**
- Status changed to Completed
- Notification sent to user about completion

### STEP 11: User Checks Completion Notification

**Request:**
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/
Authorization: Bearer USER_TOKEN
```

**Expected Response:**
Should now see notification with title "Background Check Status: Completed"

### STEP 12: User Checks Unread Count

**Request:**
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/unread-count/
Authorization: Bearer USER_TOKEN
```

**Expected Response (200 OK):**
```json
{
  "unread_count": 3
}
```

### STEP 13: User Marks Notifications as Read

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/mark-all-read/
Authorization: Bearer USER_TOKEN
```

**Expected Response (200 OK):**
```json
{
  "message": "Successfully marked 3 notifications as read",
  "count": 3
}
```

### STEP 14: Verify Unread Count is Zero

**Request:**
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/unread-count/
Authorization: Bearer USER_TOKEN
```

**Expected Response (200 OK):**
```json
{
  "unread_count": 0
}
```

## Complete Test Checklist

Use this checklist to verify everything works:

### User Flow
- [ ] User can register
- [ ] User can login and get JWT token
- [ ] User can register FCM device token
- [ ] User can submit background check request
- [ ] User receives confirmation notification (check via GET notifications)
- [ ] User can see unread count
- [ ] User receives status update notifications
- [ ] User can mark notifications as read
- [ ] User can filter notifications (is_read, category, type)

### Admin Flow
- [ ] Admin can login and get JWT token
- [ ] Admin can register FCM device token
- [ ] Admin receives notification when user submits request
- [ ] Admin can view all notifications
- [ ] Admin can update request status
- [ ] Admin status update triggers user notification
- [ ] Admin can send bulk notifications (if implemented)

### Notification System
- [ ] Notifications created on request submission
- [ ] Notifications created on status change
- [ ] Push notifications sent (check push_sent field)
- [ ] Notifications have correct type (user_to_admin, admin_to_user, system)
- [ ] Notifications have correct category (background_check)
- [ ] Related object references work (request ID)

## Debugging Tips

### If notifications are not created:

1. Check Django logs for errors
2. Verify signals are connected:
```python
python manage.py shell
from django.db.models.signals import post_save
print(post_save.receivers)
```

3. Check if request was actually created:
```
GET https://h2o427-backend-u9bx.onrender.com/api/requests/api/
Authorization: Bearer USER_TOKEN
```

4. Check database directly:
```python
python manage.py shell
from notifications.models import Notification
print(Notification.objects.all().count())
print(Notification.objects.all().values())
```

### If push notifications fail:

1. Check Firebase credentials are correct
2. Check FCM device is registered:
```
GET /api/notifications/fcm-devices/
```

3. Check push_sent field in notifications:
```python
from notifications.models import Notification
n = Notification.objects.last()
print(f"Push sent: {n.push_sent}")
print(f"Push error: {n.push_error}")
```

4. Test Firebase initialization:
```python
python manage.py shell
from notifications.firebase_service import initialize_firebase
initialize_firebase()
```

### If status change doesn't trigger notification:

1. Check that status actually changed (not just updating same value)
2. Verify signal is catching the update
3. Check Django logs for errors

## Expected Notification Flow

### When User Submits Request:
```
User submits → Request created → Signal triggered
    ↓
1. Create notification for ALL admins (user_to_admin)
2. Send push to admin devices
3. Create confirmation for user (system)
4. Send push to user device
```

### When Admin Updates Status:
```
Admin updates status → Request saved → Signal triggered
    ↓
1. Check if status changed
2. Create notification for user (admin_to_user)
3. Send push to user device
```

### When Admin Submits Report:
```
Admin submits report → Report created → Signal triggered
    ↓
1. Create notification for user (admin_to_user)
2. Send push to user device
```

## Quick Verification Commands

### Check all notifications:
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/
```

### Check only unread:
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/?is_read=false
```

### Check by category:
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/?category=background_check
```

### Check by type:
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/?type=user_to_admin
```

## Success Criteria

The notification system is working if:

1. User submits request → Admin receives notification immediately
2. Admin updates status → User receives notification immediately
3. All notifications appear in GET /api/notifications/notifications/
4. Unread count matches number of unread notifications
5. Notifications can be marked as read
6. Push notifications are sent (push_sent=True in database)
7. No errors in Django logs

## Common Issues and Solutions

**Issue:** No notifications created
**Solution:** Check signals.py is imported in apps.py ready() method

**Issue:** Duplicate notifications
**Solution:** Make sure there are no duplicate signal handlers

**Issue:** IntegrityError on push_sent
**Solution:** Make sure all Notification.objects.create() include push_sent=False

**Issue:** Status change doesn't trigger notification
**Solution:** Status must actually change (not updating from Pending to Pending)

**Issue:** Admin doesn't receive notifications
**Solution:** Make sure admin user has is_staff=True

## Next Steps

After successful testing:
1. Deploy updated code to production
2. Test with real devices
3. Monitor Django logs for any errors
4. Test with multiple users
5. Test with multiple admins
6. Verify push notifications arrive on actual devices
