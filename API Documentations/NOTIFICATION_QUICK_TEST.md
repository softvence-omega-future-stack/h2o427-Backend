# Notification System - Quick Reference

## How It Works

All notifications are AUTOMATIC via Django signals. No manual code needed.

## 3 Scenarios

### 1. User Submits Background Check Request

**Trigger:**
```
POST /api/requests/api/
```

**Who Gets Notified:**
- ALL admins receive notification
- User receives confirmation

**Notification Details:**

Admin receives:
- Title: "New Background Check Request"
- Message: "user has submitted a new background check request for John Smith."
- Type: user_to_admin
- Category: background_check

User receives:
- Title: "Background Check Request Received"
- Message: "Your background check request for John Smith has been received and is being processed."
- Type: system
- Category: background_check

---

### 2. Admin Updates Request Status

**Trigger:**
```
PUT /api/requests/api/{id}/
Body: {"status": "In Progress"}
```

**Who Gets Notified:**
- User receives status update

**Status Messages:**

"Pending":
- Title: "Background Check Status: Pending"
- Message: "Your background check request is pending review."

"In Progress":
- Title: "Background Check Status: In Progress"
- Message: "Your background check is now in progress."

"Completed":
- Title: "Background Check Status: Completed"
- Message: "Your background check has been completed!"

**Important:**
- Only triggers if status ACTUALLY changes
- Each status change creates NEW notification
- User receives notification for EACH change

---

### 3. Admin Submits Report

**Trigger:**
```
POST /api/reports/
Body: {"request": 1, "report_data": {...}}
```

**Who Gets Notified:**
- User receives report ready notification

**Notification Details:**
- Title: "Background Check Report Ready"
- Message: "Your background check report for John Smith is now available for download."
- Type: admin_to_user
- Category: report
- Includes download link in action_url

---

## Testing Each Scenario

### Test 1: User Submit Request

1. Login as user
2. Submit background check: `POST /api/requests/api/`
3. Check user notifications: `GET /api/notifications/notifications/`
4. Login as admin
5. Check admin notifications: `GET /api/notifications/notifications/`

**Expected Result:**
- User has 1 notification (confirmation)
- Each admin has 1 notification (new request)
- push_sent = true

---

### Test 2: Admin Update Status

1. Login as admin
2. Update status: `PUT /api/requests/api/1/` with `{"status": "In Progress"}`
3. Login as user
4. Check notifications: `GET /api/notifications/notifications/`
5. Update status again: `PUT /api/requests/api/1/` with `{"status": "Completed"}`
6. Check notifications again

**Expected Result:**
- User has 2 NEW notifications (1 for "In Progress", 1 for "Completed")
- push_sent = true for both

---

### Test 3: Admin Submit Report

1. Login as admin
2. Create report: `POST /api/reports/` with request_id
3. Login as user
4. Check notifications: `GET /api/notifications/notifications/`

**Expected Result:**
- User has 1 NEW notification (report ready)
- Notification has action_url with download link
- push_sent = true

---

## Quick Postman Test

### Setup
```
Base URL: https://h2o427-backend-u9bx.onrender.com
```

### Test Flow

**1. User Login**
```
POST {{base_url}}/api/auth/login/
Body: {"email": "user@example.com", "password": "password"}
Save: access token as USER_TOKEN
```

**2. Register Device (for push)**
```
POST {{base_url}}/api/notifications/fcm-devices/
Authorization: Bearer USER_TOKEN
Body: {
  "registration_token": "cvF30bCQQOWhd3ZDzdikrl:APA91b...",
  "device_type": "web"
}
```

**3. Submit Request**
```
POST {{base_url}}/api/requests/api/
Authorization: Bearer USER_TOKEN
Body: {
  "name": "Test Person",
  "dob": "1990-01-01",
  "city": "New York",
  "state": "NY",
  "email": "test@example.com",
  "phone_number": "+12125551234"
}
```

**4. Check User Notifications**
```
GET {{base_url}}/api/notifications/notifications/
Authorization: Bearer USER_TOKEN
```

**5. Admin Login**
```
POST {{base_url}}/api/auth/login/
Body: {"email": "admin@example.com", "password": "adminpass"}
Save: access token as ADMIN_TOKEN
```

**6. Check Admin Notifications**
```
GET {{base_url}}/api/notifications/notifications/
Authorization: Bearer ADMIN_TOKEN
```

**7. Update Status**
```
PUT {{base_url}}/api/requests/api/1/
Authorization: Bearer ADMIN_TOKEN
Body: {"status": "In Progress"}
```

**8. Check User Notifications Again**
```
GET {{base_url}}/api/notifications/notifications/
Authorization: Bearer USER_TOKEN
```

---

## Verification Checklist

After testing all 3 scenarios:

### Scenario 1: User Submit Request
- [ ] User notification created (title: "Background Check Request Received")
- [ ] Admin notification created (title: "New Background Check Request")
- [ ] push_sent = true for both
- [ ] GET /api/notifications/notifications/ shows notifications

### Scenario 2: Admin Update Status
- [ ] Status "In Progress" creates user notification
- [ ] Status "Completed" creates user notification
- [ ] Each status change creates SEPARATE notification
- [ ] push_sent = true
- [ ] Message matches status

### Scenario 3: Admin Submit Report
- [ ] User notification created (title: "Background Check Report Ready")
- [ ] Notification has action_url
- [ ] push_sent = true
- [ ] Category is "report"

---

## Monitoring (Django Shell)

```python
# Check all notifications
from notifications.models import Notification
print(f"Total notifications: {Notification.objects.count()}")

# Check recent notifications
for n in Notification.objects.order_by('-created_at')[:5]:
    print(f"{n.created_at} - {n.title} (push: {n.push_sent})")

# Check by category
print(f"Background check: {Notification.objects.filter(category='background_check').count()}")
print(f"Reports: {Notification.objects.filter(category='report').count()}")

# Check push failures
failed = Notification.objects.filter(push_sent=False).exclude(push_error__isnull=True)
for n in failed:
    print(f"{n.title}: {n.push_error}")
```

---

## Common Issues

**No notifications created:**
- Check signals are connected: `python manage.py shell` then `from notifications import signals`
- Verify request was actually created: `from background_requests.models import Request; Request.objects.all()`

**push_sent = False:**
- Check FCM device registered: `from notifications.models import FCMDevice; FCMDevice.objects.all()`
- Check push_error field: `Notification.objects.filter(push_sent=False).values('title', 'push_error')`

**Status change not triggering notification:**
- Status must ACTUALLY change (not updating from "Pending" to "Pending")
- Check old status vs new status in Django logs

---

## Summary

**What you need:**
1. User account
2. Admin account (is_staff=True)
3. FCM token (optional, for push)

**What happens automatically:**
1. User submits request -> Admins + User notified
2. Admin updates status -> User notified
3. Admin creates report -> User notified

**No code needed. All handled by signals.**

**Files:**
- notifications/signals.py - Handles automatic notifications
- notifications/firebase_service.py - Sends push notifications
- notifications/models.py - Stores notifications

**API Endpoints:**
- POST /api/requests/api/ - Submit request (triggers notifications)
- PUT /api/requests/api/{id}/ - Update status (triggers notifications)
- POST /api/reports/ - Create report (triggers notifications)
- GET /api/notifications/notifications/ - View notifications
