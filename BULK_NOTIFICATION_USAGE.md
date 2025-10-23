# How to Use Bulk Notification Endpoint

## Issue
You're getting: `{"recipient_ids": ["This field is required."]}`

This means the `recipient_ids` field is missing from your request.

## Solution

### Required Request Format

```json
{
    "recipient_ids": [1, 2, 3],
    "type": "admin_to_user",
    "category": "general",
    "title": "Your Notification Title",
    "message": "Your notification message here"
}
```

## Examples

### Example 1: Send to Multiple Users
```json
{
    "recipient_ids": [1, 2, 3, 4, 5],
    "type": "admin_to_user",
    "category": "general",
    "title": "System Maintenance",
    "message": "The system will be down for maintenance on Sunday."
}
```

### Example 2: Background Check Notification
```json
{
    "recipient_ids": [1],
    "type": "admin_to_user",
    "category": "background_check",
    "title": "Background Check Update",
    "message": "Your background check has been processed."
}
```

### Example 3: Payment Notification
```json
{
    "recipient_ids": [2, 3],
    "type": "admin_to_user",
    "category": "payment",
    "title": "Payment Received",
    "message": "Your payment has been successfully processed."
}
```

## How to Test

### Method 1: Swagger UI (http://127.0.0.1:8000/swagger/)

1. **Login first:**
   - Go to `/api/auth/login/` endpoint
   - Click "Try it out"
   - Enter credentials:
     ```json
     {
       "email": "admin@example.com",
       "password": "yourpassword"
     }
     ```
   - Click "Execute"
   - Copy the `access` token from response

2. **Authorize:**
   - Click the green "Authorize" button at top of page
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Click "Authorize"

3. **Test bulk-create:**
   - Find `/api/notifications/bulk-create/` endpoint
   - Click "Try it out"
   - **IMPORTANT:** Replace the example JSON with:
     ```json
     {
       "recipient_ids": [1],
       "type": "admin_to_user",
       "category": "general",
       "title": "Test Notification",
       "message": "This is a test message"
     }
     ```
   - Click "Execute"

### Method 2: cURL (PowerShell)

```powershell
# Step 1: Get token
$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login/" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"email":"admin@example.com","password":"yourpassword"}'

$token = $loginResponse.access

# Step 2: Send bulk notification
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$body = @{
    recipient_ids = @(1, 2, 3)
    type = "admin_to_user"
    category = "general"
    title = "Test Notification"
    message = "This is a test message"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/notifications/bulk-create/" `
  -Method POST `
  -Headers $headers `
  -Body $body
```

### Method 3: Using Python

```python
import requests

# Login
login_url = "http://localhost:8000/api/auth/login/"
login_data = {
    "email": "admin@example.com",
    "password": "yourpassword"
}
response = requests.post(login_url, json=login_data)
token = response.json()['access']

# Send bulk notification
bulk_url = "http://localhost:8000/api/notifications/bulk-create/"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
notification_data = {
    "recipient_ids": [1, 2, 3],
    "type": "admin_to_user",
    "category": "general",
    "title": "Test Notification",
    "message": "This is a test message"
}

response = requests.post(bulk_url, headers=headers, json=notification_data)
print(response.json())
```

## Field Reference

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `recipient_ids` | Array[Integer] | **REQUIRED** - List of user IDs | `[1, 2, 3]` |
| `title` | String | **REQUIRED** - Notification title | `"System Update"` |
| `message` | String | **REQUIRED** - Notification message | `"New features available"` |

### Optional Fields

| Field | Type | Description | Default | Options |
|-------|------|-------------|---------|---------|
| `type` | String | Notification type | `"admin_to_user"` | `admin_to_user`, `system` |
| `category` | String | Notification category | `"general"` | `background_check`, `subscription`, `payment`, `report`, `general` |
| `related_object_type` | String | Type of related object | `null` | Any string |
| `related_object_id` | Integer | ID of related object | `null` | Any integer |
| `action_url` | String | URL for action button | `null` | Any URL |

## Expected Response

**Success (201 Created):**
```json
{
    "message": "Successfully created 3 notifications",
    "count": 3
}
```

**Error (400 Bad Request):**
```json
{
    "recipient_ids": ["This field is required."]
}
```

**Error (403 Forbidden):**
```json
{
    "detail": "Only admin users can send bulk notifications"
}
```

## Common Issues

### 1. Missing recipient_ids
**Error:** `{"recipient_ids": ["This field is required."]}`

**Solution:** Make sure you include `recipient_ids` in your JSON:
```json
{
    "recipient_ids": [1, 2, 3],
    ...
}
```

### 2. Empty recipient_ids
**Error:** `{"recipient_ids": ["At least one recipient is required"]}`

**Solution:** Provide at least one user ID:
```json
{
    "recipient_ids": [1],
    ...
}
```

### 3. Invalid user IDs
**Error:** `{"recipient_ids": ["Some user IDs do not exist"]}`

**Solution:** Make sure all user IDs exist in the database. Check available users first.

### 4. Not authorized
**Error:** `{"detail": "Authentication credentials were not provided."}`

**Solution:** Make sure you're logged in and using the Bearer token in the Authorization header.

### 5. Not admin
**Error:** `{"detail": "Only admin users can send bulk notifications"}`

**Solution:** Only admin/staff users can use bulk-create. Regular users should use the regular create endpoint.

## Getting User IDs

To get a list of available user IDs:

1. **Via Admin Panel:**
   - Go to: http://127.0.0.1:8000/admin/authentication/user/
   - See list of all users with their IDs

2. **Via API (if you create one):**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/auth/users/
   ```

## Quick Test Script

Save this as `test_bulk_notification.py`:

```python
import requests
import sys

# Configuration
BASE_URL = "http://localhost:8000"
EMAIL = "admin@example.com"  # Change this
PASSWORD = "yourpassword"     # Change this

# Step 1: Login
print("Logging in...")
login_response = requests.post(
    f"{BASE_URL}/api/auth/login/",
    json={"email": EMAIL, "password": PASSWORD}
)

if login_response.status_code != 200:
    print(f"Login failed: {login_response.text}")
    sys.exit(1)

token = login_response.json()['access']
print(f"✓ Logged in successfully")

# Step 2: Send bulk notification
print("\nSending bulk notification...")
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

notification_data = {
    "recipient_ids": [1],  # Change this to actual user IDs
    "type": "admin_to_user",
    "category": "general",
    "title": "Test Bulk Notification",
    "message": "This is a test notification sent via bulk API"
}

response = requests.post(
    f"{BASE_URL}/api/notifications/bulk-create/",
    headers=headers,
    json=notification_data
)

if response.status_code == 201:
    print(f"✓ Success: {response.json()}")
else:
    print(f"✗ Error {response.status_code}: {response.text}")
```

Run it:
```bash
python test_bulk_notification.py
```

## Summary

The key point is: **You MUST include `recipient_ids` as an array of user IDs in your request body.**

Example:
```json
{
    "recipient_ids": [1, 2, 3],
    "title": "Your Title",
    "message": "Your Message"
}
```

Without `recipient_ids`, you'll get the error you're seeing.
