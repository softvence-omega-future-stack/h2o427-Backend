# Automatic Notification System

## Overview
The system now automatically sends notifications when background check requests are created, updated, or completed.

## Automatic Notifications

### 1. When User Submits a Request 

**Trigger:** User creates a new background check request

**Notifications Sent:**

#### To User (Submitter):
- **Title:** "Background Check Request Submitted"
- **Message:** "Your background check request for [Name] has been successfully submitted. We will notify you once the verification is complete."
- **Type:** System
- **Category:** Background Check
- **Push Notification:**  Yes

#### To All Admins:
- **Title:** "New Background Check Request"
- **Message:** "New background check request received from [Username] for [Name]. Status: Pending"
- **Type:** User to Admin
- **Category:** Background Check
- **Push Notification:**  Yes to all admin users

---

### 2. When Request Status Changes 

**Trigger:** Admin updates request status (Pending → In Progress → Completed)

**Notification Sent:**

#### To User:
- **Title:** "Request Status Updated"
- **Message:** "Your background check request for [Name] status has been updated to: [New Status]"
- **Type:** Admin to User
- **Category:** Background Check
- **Push Notification:**  Yes

---

### 3. When Report is Ready 
**Trigger:** Admin creates/uploads a report for a request

**Notification Sent:**

#### To User:
- **Title:** "Background Check Report Ready"
- **Message:** "Your background check report for [Name] is now ready for download."
- **Type:** Admin to User
- **Category:** Report
- **Action URL:** Direct link to download report
- **Push Notification:**  Yes

---

## Implementation Details

### Files Created/Modified:

1. **`background_requests/signals.py`** (NEW)
   - Signal handlers for Request and Report models
   - Automatically triggered on create/update

2. **`background_requests/apps.py`** (MODIFIED)
   - Added `ready()` method to import signals
   - Ensures signals are loaded when app starts

### How It Works:

```python
# Django Signals Used:
- post_save on Request model
  - created=True → New request submitted
  - created=False → Request updated (check status change)
  
- post_save on Report model
  - created=True → Report ready
```

### Signal Functions:

1. **`send_request_notifications()`**
   - Triggered when Request is created or updated
   - Checks if it's a new request or status update
   - Sends appropriate notifications

2. **`send_report_ready_notification()`**
   - Triggered when Report is created
   - Notifies user their report is ready

---

## Testing

### Test Scenario 1: New Request Submission

1. **Action:** Create a new background check request via API
   ```bash
   POST /api/requests/
   {
     "name": "John Doe",
     "dob": "1990-01-01",
     "city": "New York",
     "state": "NY",
     "email": "john@example.com",
     "phone_number": "1234567890"
   }
   ```

2. **Expected Results:**
   -  User receives: "Request Submitted Successfully"
   -  Admins receive: "New Request Received"
   -  Both notifications appear in `/api/notifications/test/`
   -  Push notifications sent (if devices registered)

### Test Scenario 2: Status Update

1. **Action:** Admin updates request status
   ```bash
   PATCH /api/requests/{id}/
   {
     "status": "In Progress"
   }
   ```

2. **Expected Results:**
   -  User receives: "Request Status Updated"
   -  Notification shows new status
   -  Push notification sent

### Test Scenario 3: Report Ready

1. **Action:** Admin creates report
   ```bash
   POST /api/requests/{id}/submit-report/
   {
     "report_data": {...}
   }
   ```

2. **Expected Results:**
   -  User receives: "Background Check Report Ready"
   -  Notification includes download link
   -  Push notification sent

---

## Notification Data Stored

Each notification includes:

- **recipient:** User who receives notification
- **sender:** User who triggered it (or None for system)
- **type:** admin_to_user / user_to_admin / system
- **category:** background_check / report / general / etc.
- **title:** Notification title
- **message:** Notification body
- **related_object_type:** "Request" or "Report"
- **related_object_id:** ID of the related object
- **action_url:** Optional URL for action button
- **is_read:** Read status
- **push_sent:** Whether push was sent
- **push_sent_at:** When push was sent
- **push_error:** Any push errors

---

## Viewing Notifications

### For Users:
- **Web UI:** http://127.0.0.1:8000/api/notifications/test/
- **API:** `GET /api/notifications/notifications/`
- **Mobile App:** Push notifications + in-app list

### For Admins:
- **Web UI:** http://127.0.0.1:8000/api/notifications/all/
- **API:** `GET /api/notifications/notifications/`
- **Admin Panel:** Django admin

---

## Push Notification Data Payload

### Request Created:
```json
{
  "notification_id": "123",
  "request_id": "456",
  "type": "request_created"
}
```

### Status Update:
```json
{
  "notification_id": "124",
  "request_id": "456",
  "status": "In Progress",
  "type": "status_update"
}
```

### Report Ready:
```json
{
  "notification_id": "125",
  "request_id": "456",
  "report_id": "789",
  "type": "report_ready"
}
```

### New Request (Admin):
```json
{
  "request_id": "456",
  "user_id": "1",
  "type": "new_request"
}
```

---

## Error Handling

All push notification failures are caught and logged:
- User notifications are created in database even if push fails
- Failed device tokens are automatically deactivated
- Error messages stored in notification record

---

## Configuration

### Required:
- Firebase credentials configured in `.env`
- FCM devices registered for push notifications
- Signals loaded (automatic via apps.py)

### Optional:
- Customize notification messages in `signals.py`
- Add more notification types for other events
- Configure notification preferences per user

---

## Future Enhancements

Possible additions:
- [ ] Email notifications (in addition to push)
- [ ] SMS notifications for critical updates
- [ ] User notification preferences
- [ ] Notification batching/digest
- [ ] Rich notifications with images
- [ ] Action buttons in notifications
- [ ] Scheduled notifications
- [ ] Notification templates

---

The automatic notification system is now live and will trigger on all new requests, status changes, and report completions!
