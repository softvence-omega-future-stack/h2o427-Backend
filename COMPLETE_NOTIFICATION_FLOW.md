# Complete Notification Flow - Background Check System

##  Overview
Automatic notifications are sent at every stage of the background check process.

---

##  Complete User Journey with Notifications

### Stage 1: User Submits Request 

**User Action:**
- User fills out background check form
- Clicks "Submit Request"
- Request is created in the database

**Automatic Notifications:**

####  User Receives:
```
Title: "Background Check Request Submitted"
Message: "Your background check request for [Name] has been successfully 
         submitted. We will notify you once the verification is complete."
Type: System Notification
Push: Yes
```

#### 📱 All Admins Receive:
```
Title: "New Background Check Request"
Message: "New background check request received from [Username] for [Name]. 
         Status: Pending"
Type: User to Admin
Push:  Yes
```

---

### Stage 2: Admin Updates Status 

**Admin Action:**
- Admin reviews the request
- Changes status from "Pending" → "In Progress"

**Automatic Notification:**

#### 📱 User Receives:
```
Title: "Request Status Updated"
Message: "Your background check request for [Name] status has been 
         updated to: In Progress"
Type: Admin to User
Push:  Yes
```

---

### Stage 3: Admin Submits Report 

**Admin Action:**
- Admin completes background check
- Submits/uploads report through admin panel or API
- Report is created in the database

**Automatic Notification:**

#### 📱 User Receives:
```
Title: "Background Check Report Ready"
Message: "Your background check report for [Name] is now ready for download."
Type: Admin to User
Category: Report
Action: Direct download link included
Push: Yes
```

---

### Stage 4: Admin Marks as Completed 

**Admin Action:**
- Admin changes status to "Completed"

**Automatic Notification:**

#### 📱 User Receives:
```
Title: "Request Status Updated"
Message: "Your background check request for [Name] status has been 
         updated to: Completed"
Type: Admin to User
Push:  Yes
```

---

##  Notification Summary Table

| Event | User Gets | Admin Gets | Push | In-App |
|-------|-----------|------------|------|--------|
| Request Submitted | ✅ Success message | ✅ New request alert | ✅ | ✅ |
| Status Changed | ✅ Status update | ❌ | ✅ | ✅ |
| Report Submitted | ✅ Report ready | ❌ | ✅ | ✅ |
| Request Completed | ✅ Completion notice | ❌ | ✅ | ✅ |

---

## 🧪 How to Test

### Test 1: Submit a Request

**Using API:**
```bash
POST http://127.0.0.1:8000/api/requests/
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "name": "John Doe",
  "dob": "1990-01-01",
  "city": "New York",
  "state": "NY",
  "email": "john@example.com",
  "phone_number": "1234567890"
}
```

**Expected:**
1. User sees success message
2. Check notifications: `GET /api/notifications/notifications/`
3. Should see "Request Submitted" notification
4. Check admin panel - admins should see "New Request" notification

---

### Test 2: Update Status

**Using Admin Panel or API:**
```bash
PATCH http://127.0.0.1:8000/api/admin/requests/{id}/update-status/
Content-Type: application/json
Authorization: Bearer ADMIN_TOKEN

{
  "status": "In Progress"
}
```

**Expected:**
1. User receives "Status Updated" notification
2. Check: `GET /api/notifications/notifications/` (as user)
3. Should see status change notification

---

### Test 3: Submit Report

**Using Admin API:**
```bash
POST http://127.0.0.1:8000/api/requests/{id}/submit-report/
Content-Type: application/json
Authorization: Bearer ADMIN_TOKEN

{
  "ssn_validation": "Valid & Matches Records",
  "criminal_records": "No records found",
  "final_summary": "Candidate has passed all checks"
}
```

**Expected:**
1. User receives "Report Ready" notification
2. Notification includes download link
3. Check: `GET /api/notifications/notifications/` (as user)
4. Should see report ready notification

---

## 📱 Push Notification Details

### For Mobile/Web Apps

**When receiving notifications:**

#### Request Submitted:
```javascript
{
  title: "Request Submitted Successfully",
  body: "Your background check request for John Doe has been received...",
  data: {
    notification_id: "123",
    request_id: "456",
    type: "request_created"
  }
}
```

#### Report Ready:
```javascript
{
  title: "Report Ready",
  body: "Your background check report for John Doe is ready!",
  data: {
    notification_id: "124",
    request_id: "456",
    report_id: "789",
    type: "report_ready"
  }
}
```

#### Admin - New Request:
```javascript
{
  title: "New Request Received",
  body: "New background check request from john_user for John Doe",
  data: {
    request_id: "456",
    user_id: "1",
    type: "new_request"
  }
}
```

---

## 🔍 View Notifications

### Web Interface:
- **Test Page:** http://127.0.0.1:8000/api/notifications/test/
- **All Notifications:** http://127.0.0.1:8000/api/notifications/all/

### API Endpoints:
- **List:** `GET /api/notifications/notifications/`
- **Unread Count:** `GET /api/notifications/notifications/unread-count/`
- **Mark as Read:** `POST /api/notifications/notifications/mark-read/`
- **Mark All Read:** `POST /api/notifications/notifications/mark-all-read/`

---

## 💾 Database Storage

Each notification stores:
- **recipient** - User receiving notification
- **sender** - User who triggered it (or null for system)
- **type** - admin_to_user / user_to_admin / system
- **category** - background_check / report / general / etc.
- **title** - Notification headline
- **message** - Full notification text
- **related_object_type** - "Request" or "Report"
- **related_object_id** - ID of related object
- **action_url** - Download link (for reports)
- **is_read** - Read/unread status
- **push_sent** - Whether push was sent
- **push_sent_at** - Timestamp of push
- **push_error** - Any errors
- **created_at** - When notification was created

---

## ⚙️ Technical Implementation

### Files:
1. **`background_requests/signals.py`**
   - `send_request_notifications()` - Handles request create/update
   - `send_report_ready_notification()` - Handles report creation

2. **`background_requests/apps.py`**
   - Loads signals automatically on app startup

3. **`notifications/firebase_service.py`**
   - `send_notification_to_user()` - Send to specific user
   - `send_notification_to_admins()` - Send to all admins

### Signal Triggers:
```python
# Request created → User + Admin notifications
post_save(sender=Request, created=True)

# Request updated → User notification (if status changed)
post_save(sender=Request, created=False)

# Report created → User notification
post_save(sender=Report, created=True)
```

---

## 📈 Example Flow

```
1. User submits request
   └─> User gets: "Request Submitted" ✅
   └─> Admin gets: "New Request" ✅

2. Admin changes status to "In Progress"
   └─> User gets: "Status Updated: In Progress" ✅

3. Admin submits report
   └─> User gets: "Report Ready" with download link ✅
   └─> Request status auto-changes to "Completed"
   └─> User gets: "Status Updated: Completed" ✅

4. User downloads report
   └─> Can mark notification as read
```

---

## 🚀 Status: LIVE & WORKING

The notification system is fully implemented and active! 

**Test it now:**
1. Create a new background check request
2. Check notifications at `/api/notifications/test/`
3. See both user and admin notifications created automatically!

All notifications are working automatically! 🎉
