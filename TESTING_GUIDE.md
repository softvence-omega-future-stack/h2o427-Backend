# Notification System Testing Guide

## Overview

Your notification system automatically sends notifications for 3 scenarios:
1. When User Submits Background Check Request
2. When Admin Updates Request Status
3. When Admin Submits Report

## Prerequisites

- Backend running at: https://h2o427-backend-u9bx.onrender.com (or local)
- User account (regular user)
- Admin account (with is_staff=True)
- FCM token from your device

---

## Scenario 1: User Submits Background Check Request

### What Happens Automatically

When a user submits a background check request:

1. Database notification created for ALL admins
2. Database notification created for the user (confirmation)
3. Push notification sent to all admin devices
4. Push notification sent to user's device

### Step-by-Step Test

#### Step 1: Login as User

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "userpassword"
}
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

Save the `access` token as USER_TOKEN.

#### Step 2: Register User's Device (Optional but needed for push)

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/notifications/fcm-devices/
Authorization: Bearer USER_TOKEN
Content-Type: application/json

{
  "registration_token": "cvF30bCQQOWhd3ZDzdikrl:APA91bFTeDckJySEQ989h7r2Fb8WCFl8j2LejX8MEUjYuVJv0xsX-UIhhmjCCV0q3yaxL9ZaWJ7YiePLVGOHZW1QageWJaZnVIx0-MvPS2q_2xzWMyaCbsI",
  "device_type": "web"
}
```

#### Step 3: Submit Background Check Request

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/requests/api/
Authorization: Bearer USER_TOKEN
Content-Type: application/json

{
  "name": "John Smith",
  "dob": "1990-05-15",
  "city": "New York",
  "state": "NY",
  "email": "john.smith@example.com",
  "phone_number": "+12125551234"
}
```

**Response:**
```json
{
  "id": 1,
  "user": 1,
  "name": "John Smith",
  "status": "Pending",
  "created_at": "2025-11-08T10:00:00Z"
}
```

#### Step 4: Verify User Notification

**Request:**
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/
Authorization: Bearer USER_TOKEN
```

**Expected Response:**
```json
[
  {
    "id": 2,
    "recipient": 1,
    "sender": null,
    "type": "system",
    "category": "background_check",
    "title": "Background Check Request Received",
    "message": "Your background check request for John Smith has been received and is being processed.",
    "is_read": false,
    "push_sent": true,
    "push_sent_at": "2025-11-08T10:00:01Z",
    "created_at": "2025-11-08T10:00:01Z"
  }
]
```

#### Step 5: Verify Admin Notification

Login as admin:

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/auth/login/
Content-Type: application/json

{
  "email": "admin@example.com",
  "password": "adminpassword"
}
```

Save the `access` token as ADMIN_TOKEN.

Check admin notifications:

**Request:**
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/
Authorization: Bearer ADMIN_TOKEN
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "recipient": 2,
    "sender": 1,
    "sender_details": {
      "id": 1,
      "username": "user",
      "email": "user@example.com"
    },
    "type": "user_to_admin",
    "category": "background_check",
    "title": "New Background Check Request",
    "message": "user has submitted a new background check request for John Smith.",
    "is_read": false,
    "push_sent": true,
    "action_url": "/admin/background_requests/request/1/change/",
    "created_at": "2025-11-08T10:00:00Z"
  }
]
```

### What to Verify

- User receives confirmation notification
- All admins receive new request notification
- push_sent = true for both notifications
- Notification appears in user's device (if FCM token registered)
- Notification appears in admin's device (if FCM token registered)

---

## Scenario 2: Admin Updates Request Status

### What Happens Automatically

When admin updates request status:

1. System detects status change
2. Database notification created for the user
3. Push notification sent to user's device

### Step-by-Step Test

#### Step 1: Admin Updates Status to "In Progress"

**Request:**
```
PUT https://h2o427-backend-u9bx.onrender.com/api/requests/api/1/
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json

{
  "status": "In Progress"
}
```

**Response:**
```json
{
  "id": 1,
  "status": "In Progress",
  "updated_at": "2025-11-08T10:05:00Z"
}
```

#### Step 2: Verify User Notification

**Request:**
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/?is_read=false
Authorization: Bearer USER_TOKEN
```

**Expected Response:**
```json
[
  {
    "id": 3,
    "recipient": 1,
    "sender": null,
    "type": "admin_to_user",
    "category": "background_check",
    "title": "Background Check Status: In Progress",
    "message": "Your background check is now in progress.",
    "is_read": false,
    "push_sent": true,
    "push_sent_at": "2025-11-08T10:05:01Z",
    "created_at": "2025-11-08T10:05:01Z"
  }
]
```

#### Step 3: Update Status to "Completed"

**Request:**
```
PUT https://h2o427-backend-u9bx.onrender.com/api/requests/api/1/
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json

{
  "status": "Completed"
}
```

#### Step 4: Verify Completion Notification

**Request:**
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/
Authorization: Bearer USER_TOKEN
```

**Expected Response:**
```json
[
  {
    "id": 4,
    "title": "Background Check Status: Completed",
    "message": "Your background check has been completed!",
    "type": "admin_to_user",
    "category": "background_check",
    "push_sent": true,
    "created_at": "2025-11-08T10:10:00Z"
  }
]
```

### What to Verify

- User receives notification for EACH status change
- Status changes: Pending -> In Progress -> Completed
- Each change creates separate notification
- push_sent = true
- User sees notification on device

---

## Scenario 3: Admin Submits Report

### What Happens Automatically

When admin creates a report:

1. Database notification created for the user
2. Push notification sent to user's device
3. User can download the report

### Step-by-Step Test

#### Step 1: Admin Creates Report

**Request:**
```
POST https://h2o427-backend-u9bx.onrender.com/api/reports/
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json

{
  "request": 1,
  "report_data": {
    "criminal_record": "None",
    "employment_verification": "Verified",
    "education_verification": "Verified"
  },
  "status": "Completed"
}
```

**Response:**
```json
{
  "id": 1,
  "request": 1,
  "status": "Completed",
  "created_at": "2025-11-08T10:15:00Z"
}
```

#### Step 2: Verify User Notification

**Request:**
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/
Authorization: Bearer USER_TOKEN
```

**Expected Response:**
```json
[
  {
    "id": 5,
    "recipient": 1,
    "sender": null,
    "type": "admin_to_user",
    "category": "report",
    "title": "Background Check Report Ready",
    "message": "Your background check report for John Smith is now available for download.",
    "is_read": false,
    "push_sent": true,
    "action_url": "/api/reports/1/download/",
    "created_at": "2025-11-08T10:15:01Z"
  }
]
```

### What to Verify

- User receives report ready notification
- push_sent = true
- action_url contains download link
- User sees notification on device

---

## Testing with Django Management Command

Quick test without Postman:

```bash
python manage.py test_notifications --email user@example.com --fcm-token "YOUR_FCM_TOKEN"
```

This will:
- Create a test notification
- Send push notification
- Show results

---

## Complete Test Flow (All 3 Scenarios)

### 1. Setup

```bash
# Terminal 1: Start Django server
python manage.py runserver

# Terminal 2: Open Django shell for monitoring
python manage.py shell
```

In shell:
```python
from notifications.models import Notification
from background_requests.models import Request

# Watch notifications in real-time
def watch_notifications():
    count = Notification.objects.count()
    print(f"Current notifications: {count}")
    for n in Notification.objects.order_by('-created_at')[:5]:
        print(f"- {n.title} (push_sent: {n.push_sent})")

# Run this after each test
watch_notifications()
```

### 2. Test User Submit Request

1. Login as user
2. Register FCM device
3. Submit background check request
4. Check user notifications via API
5. Check admin notifications via API

4. Run `watch_notifications()` in shell
Expected notifications: 2 (1 for user, 1 for each admin)

### 3. Test Admin Update Status

1. Login as admin
2. Update request status to "In Progress"
3. Run `watch_notifications()` in shell
4. Check user notifications via API

Expected notifications: +1 (status update for user)

5. Update status to "Completed"
6. Run `watch_notifications()` in shell
7. Check user notifications via API

Expected notifications: +1 (completion for user)

### 4. Test Admin Submit Report

1. Login as admin
2. Create report for request
3. Run `watch_notifications()` in shell
4. Check user notifications via API

Expected notifications: +1 (report ready for user)

---

## Verification Checklist

### User Submits Request
- [ ] User receives confirmation notification
- [ ] Admin receives new request notification
- [ ] Both notifications have push_sent = true
- [ ] Notifications visible via GET /api/notifications/notifications/

### Admin Updates Status
- [ ] User receives status update notification
- [ ] Notification has correct status in title
- [ ] push_sent = true
- [ ] Each status change creates separate notification

### Admin Submits Report
- [ ] User receives report ready notification
- [ ] Notification includes download link in action_url
- [ ] push_sent = true
- [ ] Notification category is "report"

---

## Quick Postman Test Collection

Import this JSON into Postman:

```json
{
  "info": {
    "name": "H2O427 Notification Testing",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "base_url",
      "value": "https://h2o427-backend-u9bx.onrender.com"
    }
  ],
  "item": [
    {
      "name": "1. User Login",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.environment.set('user_token', pm.response.json().access);"
            ]
          }
        }
      ],
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "raw",
          "raw": "{\"email\": \"user@example.com\", \"password\": \"password\"}",
          "options": {"raw": {"language": "json"}}
        },
        "url": "{{base_url}}/api/auth/login/"
      }
    },
    {
      "name": "2. Register User Device",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Authorization", "value": "Bearer {{user_token}}"}
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"registration_token\": \"YOUR_FCM_TOKEN\", \"device_type\": \"web\"}",
          "options": {"raw": {"language": "json"}}
        },
        "url": "{{base_url}}/api/notifications/fcm-devices/"
      }
    },
    {
      "name": "3. Submit Background Check",
      "request": {
        "method": "POST",
        "header": [
          {"key": "Authorization", "value": "Bearer {{user_token}}"}
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"name\": \"John Smith\", \"dob\": \"1990-01-01\", \"city\": \"New York\", \"state\": \"NY\", \"email\": \"test@example.com\", \"phone_number\": \"+12125551234\"}",
          "options": {"raw": {"language": "json"}}
        },
        "url": "{{base_url}}/api/requests/api/"
      }
    },
    {
      "name": "4. Get User Notifications",
      "request": {
        "method": "GET",
        "header": [
          {"key": "Authorization", "value": "Bearer {{user_token}}"}
        ],
        "url": "{{base_url}}/api/notifications/notifications/"
      }
    },
    {
      "name": "5. Admin Login",
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.environment.set('admin_token', pm.response.json().access);"
            ]
          }
        }
      ],
      "request": {
        "method": "POST",
        "header": [],
        "body": {
          "mode": "raw",
          "raw": "{\"email\": \"admin@example.com\", \"password\": \"adminpassword\"}",
          "options": {"raw": {"language": "json"}}
        },
        "url": "{{base_url}}/api/auth/login/"
      }
    },
    {
      "name": "6. Get Admin Notifications",
      "request": {
        "method": "GET",
        "header": [
          {"key": "Authorization", "value": "Bearer {{admin_token}}"}
        ],
        "url": "{{base_url}}/api/notifications/notifications/"
      }
    },
    {
      "name": "7. Update Status (In Progress)",
      "request": {
        "method": "PUT",
        "header": [
          {"key": "Authorization", "value": "Bearer {{admin_token}}"}
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"status\": \"In Progress\"}",
          "options": {"raw": {"language": "json"}}
        },
        "url": "{{base_url}}/api/requests/api/1/"
      }
    },
    {
      "name": "8. Update Status (Completed)",
      "request": {
        "method": "PUT",
        "header": [
          {"key": "Authorization", "value": "Bearer {{admin_token}}"}
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"status\": \"Completed\"}",
          "options": {"raw": {"language": "json"}}
        },
        "url": "{{base_url}}/api/requests/api/1/"
      }
    }
  ]
}
```

---

## Troubleshooting

### Notifications not created
Check Django shell:
```python
from notifications.models import Notification
print(Notification.objects.count())
```

### Push not sent (push_sent = False)
Check notification errors:
```python
from notifications.models import Notification
for n in Notification.objects.filter(push_sent=False):
    print(f"{n.title}: {n.push_error}")
```

### FCM token issues
Verify device registered:
```python
from notifications.models import FCMDevice
from authentication.models import User
user = User.objects.get(email='user@example.com')
print(FCMDevice.objects.filter(user=user, active=True))
```

---

## Summary

Notification Flow:

1. User submits request -> Admins + User notified
2. Admin updates status -> User notified
3. Admin creates report -> User notified

All automatic via Django signals.
No manual triggering needed.
Push notifications sent to all registered devices.
