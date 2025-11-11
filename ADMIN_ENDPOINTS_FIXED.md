# Admin Endpoints - All Issues Fixed

All missing admin endpoints have been implemented and registered. This document lists all working admin endpoints.

---

## Dashboard Endpoints

### 1. Dashboard Statistics
**GET** `/api/admin/dashboard/stats/`

Returns:
- Total requests count
- Pending/In Progress/Completed counts
- Total clients
- Recent requests (last 5)
- Recent activities (last 10)

Status: WORKING (Fixed AttributeError)

---

### 2. Request Management
**GET** `/api/admin/dashboard/requests/`

Query Parameters:
- `status`: pending, in_progress, completed, cancelled
- `assigned_to`: admin user ID
- `search`: Search by user name, email, or subject name

Returns: List of all requests with filtering

Status: WORKING

---

### 3. Request Detail
**GET** `/api/admin/dashboard/requests/<request_id>/`

Returns:
- Full request details
- Associated user information
- Report details (if available)
- Activity history
- Notes
- Assignment information

Status: WORKING

---

### 4. Update Request Status
**PATCH** `/api/admin/dashboard/requests/<request_id>/status/`

Request Body:
```json
{
  "status": "in_progress",
  "notes": "Optional notes about status change"
}
```

**Valid Status Values:**
- `"pending"` or `"Pending"`
- `"in_progress"` or `"In Progress"`
- `"completed"` or `"Completed"`

Status: WORKING (Fixed - Now accepts both formats)

---

### 5. Bulk Status Update
**PATCH** `/api/admin/dashboard/requests/bulk-status/`

Request Body:
```json
{
  "request_ids": [1, 2, 3],
  "status": "in_progress"
}
```

**Valid Status Values:**
- `"pending"` or `"Pending"`
- `"in_progress"` or `"In Progress"`
- `"completed"` or `"Completed"`

Status: WORKING (Fixed - Now accepts both formats)

---

### 6. Add Request Note
**POST** `/api/admin/dashboard/requests/<request_id>/notes/`

Request Body:
```json
{
  "note": "Important note about this request",
  "is_internal": true
}
```

**Fields:**
- `note` (required): The note text
- `is_internal` (optional): Boolean, default `true`. Set to `false` for notes visible to clients

**Note:** The `request` and `admin_user` fields are automatically set from the URL and authenticated user.

Status: WORKING (Fixed - Serializer fields corrected)

---

### 7. Assign Request
**POST** `/api/admin/dashboard/requests/<request_id>/assign/`

Request Body:
```json
{
  "assigned_to": 2,
  "priority": "high",
  "due_date": "2024-12-31",
  "notes": "Urgent case"
}
```



**PATCH** `/api/admin/dashboard/requests/<request_id>/assign/`

Update existing assignment with same fields.

**Note:** The `request` and `assigned_by` fields are automatically set from the URL and authenticated user.

Status: WORKING (Fixed - Better error messages added)

---

### 8. Admin Users List
**GET** `/api/admin/dashboard/users/`

Returns: List of all admin/staff users

Status: WORKING

---

### 9. Download Report PDF (NEW)
**GET** `/api/admin/dashboard/requests/<request_id>/report/download/`

Downloads the PDF report file for a specific request.

Returns: PDF file with appropriate headers

Status: NEWLY IMPLEMENTED

---

### 10. All Users List (NEW)
**GET** `/api/admin/dashboard/all-users/`

Query Parameters:
- `search`: Search by name or email
- `subscription_plan`: Filter by plan name

Returns:
```json
{
  "count": 10,
  "results": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "subscription_plan": "Basic Plan",
      "start_date": "2024-01-01",
      "requests": 5,
      "total_reports_purchased": 10,
      "total_reports_used": 5,
      "available_reports": 5,
      "status": "active"
    }
  ]
}
```

Status: WORKING (Fixed - select_related issue resolved)

---

### 11. User Detail (NEW)
**GET** `/api/admin/dashboard/all-users/<user_id>/`

Returns:
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "subscription": { ... },
  "requests": [ ... ],
  "date_joined": "2024-01-01T00:00:00Z"
}
```

Status: NEWLY IMPLEMENTED

---

## Plan Management Endpoints (NEW)

### 12. List All Plans
**GET** `/api/admin/plans/`

Query Parameters:
- `include_inactive` (optional): Set to 'true' to include soft-deleted plans

Returns: List of subscription plans (active only by default)

Response Format:
```json
{
  "plans": [...],
  "count": 3,
  "showing_inactive": false
}
```

Status: **WORKING (Fixed - Now filters by is_active)**

---

### 13. Create New Plan
**POST** `/api/admin/plans/`

Request Body:
```json
{
  "name": "Enterprise Plan",
  "plan_type": "premium",
  "price_per_report": 50.00,
  "description": "Premium background check with all features",
  "identity_verification": true,
  "ssn_trace": true,
  "national_criminal_search": true,
  "sex_offender_registry": true,
  "employment_verification": true,
  "education_verification": true,
  "unlimited_county_search": true,
  "priority_support": true,
  "api_access": false
}
```

Status: NEWLY IMPLEMENTED

---

### 14. Get Plan Details
**GET** `/api/admin/plans/<plan_id>/`

Returns: Detailed plan information

Status: NEWLY IMPLEMENTED

---

### 15. Update Plan
**PATCH** `/api/admin/plans/<plan_id>/`

Request Body: (any plan fields to update)
```json
{
  "price_per_report": 55.00,
  "description": "Updated description",
  "priority_support": true
}
```

Status: NEWLY IMPLEMENTED

---

### 16. Delete Plan
**DELETE** `/api/admin/plans/<plan_id>/`

Query Parameters:
- `hard_delete` (optional): Set to 'true' for permanent deletion

**Soft Delete (Default):**
- Sets `is_active=False`
- Plan remains in database
- Can be viewed with `?include_inactive=true`

**Hard Delete (`?hard_delete=true`):**
- Permanently removes plan from database
- Blocked if plan has active subscriptions
- Returns error with subscription count

Response Examples:
```json
// Soft delete
{
  "message": "Plan \"Basic Plan\" deactivated (soft delete)",
  "is_active": false,
  "note": "Use ?hard_delete=true to permanently delete this plan"
}

// Hard delete success
{
  "message": "Plan \"Basic Plan\" permanently deleted",
  "deleted": true
}

// Hard delete blocked
{
  "error": "Cannot delete plan. 5 users are currently subscribed to this plan.",
  "active_subscriptions": 5
}
```

Status: **WORKING (Fixed - Now properly filters list and supports hard delete)**

---

### 17. Toggle Plan Status
**POST** `/api/admin/plans/<plan_id>/toggle-status/`

Toggles between active/inactive status

Returns:
```json
{
  "message": "Plan activated successfully",
  "is_active": true
}
```

Status: NEWLY IMPLEMENTED

---

## Notification Endpoints (NEW)

### 18. Get Admin Notifications
**GET** `/api/notifications/admin/`

Query Parameters:
- `unread_only`: true/false

Returns:
```json
{
  "count": 5,
  "unread_count": 2,
  "results": [
    {
      "id": 1,
      "title": "New Request",
      "message": "New background check request received",
      "is_read": false,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

Status: WORKING (Fixed - Changed user to recipient field)

---

### 19. Mark Notification as Read
**POST** `/api/notifications/admin/<notification_id>/mark-read/`

Marks a specific notification as read

Status: WORKING (Fixed - Changed user to recipient field)

---

### 20. Mark All Notifications as Read
**POST** `/api/notifications/admin/mark-all-read/`

Marks all notifications as read for the current admin user

Returns:
```json
{
  "message": "5 notifications marked as read",
  "count": 5
}
```

Status: WORKING (Fixed - Changed user to recipient field)

---

## Report Management Endpoints

### 21. List All Reports
**GET** `/api/admin/reports/`

Returns list of all generated reports with request details

Response:
```json
[
  {
    "id": 1,
    "request": 1,
    "request_name": "Background Check for John Doe",
    "request_status": "Completed",
    "client_name": "John Doe",
    "pdf": "/media/reports/report_1.pdf",
    "generated_at": "2024-01-20T15:30:00Z",
    "notes": "Background check completed"
  }
]
```

Status: WORKING

---

### 22. Upload Report PDF
**POST** `/api/admin/reports/`

**Content-Type:** `multipart/form-data`

Form Data Fields:
- `request_id` (required): Integer - Background check request ID
- `pdf` (required): File - PDF report file
- `notes` (optional): String - Additional notes


Example using Postman:
1. Select POST method
2. Set URL to `/api/admin/reports/`
3. Go to "Body" tab
4. Select "form-data"
5. Add key "request_id" with value (e.g., 67)
6. Add key "pdf" and change type to "File", then select your PDF
7. Add key "notes" with your notes text

Response:
```json
{
  "message": "Report uploaded successfully",
  "report": {
    "id": 1,
    "request": 67,
    "request_name": "Background Check",
    "request_status": "Completed",
    "client_name": "John Doe",
    "pdf": "/media/reports/report_67.pdf",
    "generated_at": "2024-01-20T15:30:00Z",
    "notes": "Background check completed"
  }
}
```


## Notes
```bash
POST http://127.0.0.1:8000/api/admin/dashboard/requests/54/notes/
{
  "note": "Important note about this request",
  "is_internal": true
}
```
**Response:**
```json
{
  "id": 1,
  "request": 54,
  "request_name": "John Doe",
  "admin_user": 1,
  "admin_username": "admin",
  "admin_full_name": "Admin User",
  "note": "Important note about this request",
  "is_internal": true,
  "created_at": "2024-11-11T10:00:00Z",
  "updated_at": "2024-11-11T10:00:00Z"
}
```

```bash
POST http://127.0.0.1:8000/api/admin/dashboard/requests/54/assign/
{
  "assigned_to": 2,
  "priority": "high",
  "due_date": "2024-12-31",
  "notes": "Urgent case"
}
```

**Response:**
```json
{
  "id": 1,
  "request": 54,
  "request_name": "John Doe",
  "assigned_to": 2,
  "assigned_to_username": "jane_admin",
  "assigned_to_full_name": "Jane Admin",
  "assigned_by": 1,
  "assigned_by_username": "admin",
  "assigned_at": "2024-11-11T10:00:00Z",
  "due_date": "2024-12-31",
  "priority": "high",
  "notes": "Urgent case"
}
```




**Note:** Uploading a report automatically sets the request status to "Completed"

Status: WORKING

---


