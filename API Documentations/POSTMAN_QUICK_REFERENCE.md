# Quick Reference - Postman Testing

## Your Credentials

FCM Token:
```
cvF30bCQQOWhd3ZDzdikrl:APA91bFTeDckJySEQ989h7r2Fb8WCFl8j2LejX8MEUjYuVJv0xsX-UIhhmjCCV0q3yaxL9ZaWJ7YiePLVGOHZW1QageWJaZnVIx0-MvPS2q_2xzWMyaCbsI
```

Device Token:
```
BE2A.250530.026.D1
```

Server URL:
```
https://h2o427-backend-u9bx.onrender.com
```

## Essential Tests (Copy & Paste)

### 1. Login
```
POST https://h2o427-backend-u9bx.onrender.com/api/auth/login/
Content-Type: application/json

{
  "email": "your-email@example.com",
  "password": "your-password"
}
```

### 2. Register Device
```
POST https://h2o427-backend-u9bx.onrender.com/api/notifications/fcm-devices/
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "registration_token": "cvF30bCQQOWhd3ZDzdikrl:APA91bFTeDckJySEQ989h7r2Fb8WCFl8j2LejX8MEUjYuVJv0xsX-UIhhmjCCV0q3yaxL9ZaWJ7YiePLVGOHZW1QageWJaZnVIx0-MvPS2q_2xzWMyaCbsI",
  "device_type": "web"
}
```

### 3. List Devices
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/fcm-devices/
Authorization: Bearer YOUR_TOKEN
```

### 4. Get Notifications
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/
Authorization: Bearer YOUR_TOKEN
```

### 5. Get Unread Count
```
GET https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/unread-count/
Authorization: Bearer YOUR_TOKEN
```

### 6. Mark as Read
```
POST https://h2o427-backend-u9bx.onrender.com/api/notifications/notifications/mark-read/
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "notification_ids": [1, 2],
  "is_read": true
}
```

### 7. Submit Background Check (Triggers Notification)
```
POST https://h2o427-backend-u9bx.onrender.com/api/requests/api/
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json

{
  "name": "nowshi",
  "date_of_birth": "1990-01-15",
  "ssn": "123-45-6789",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "zip_code": "10001",
  "country": "USA"
}
```

## All Endpoints

**Device Management:**
```
POST   /api/notifications/fcm-devices/              Register
GET    /api/notifications/fcm-devices/              List
DELETE /api/notifications/fcm-devices/{id}/         Delete
POST   /api/notifications/fcm-devices/deactivate-all/  Deactivate all
```

**Notifications:**
```
GET    /api/notifications/notifications/            List
GET    /api/notifications/notifications/unread-count/  Count
POST   /api/notifications/notifications/mark-read/  Mark read
POST   /api/notifications/notifications/mark-all-read/  Mark all
DELETE /api/notifications/notifications/clear-read/  Clear read
```

**Filters:**
```
?is_read=false
?type=admin_to_user
?category=background_check
```

## Testing Flow

1. Login (get token)
2. Register FCM device
3. Submit background check request
4. Check notifications (should see confirmation)
5. Check unread count (should be 1+)
6. Mark as read
7. Verify count decreased

## Expected Results

After registering device:
- Status 201 Created
- Returns device ID

After submitting request:
- Status 201 Created
- Notification automatically created
- Push sent to device

After checking notifications:
- Status 200 OK
- Array of notification objects
- Shows title, message, read status

## Common Issues

**401 Unauthorized:**
- Token missing or expired
- Solution: Login again

**400 Bad Request:**
- Invalid JSON or missing fields
- Check request body

**Token expired:**
- Lifetime: 30 minutes
- Solution: Re-login

## Quick Test Script

1. Open Postman
2. Create new request
3. Set method to POST
4. URL: `https://h2o427-backend-u9bx.onrender.com/api/auth/login/`
5. Headers: `Content-Type: application/json`
6. Body: Raw JSON with email/password
7. Send
8. Copy `access` token from response
9. Create new request
10. Set method to POST
11. URL: `https://h2o427-backend-u9bx.onrender.com/api/notifications/fcm-devices/`
12. Headers:
    - `Authorization: Bearer YOUR_COPIED_TOKEN`
    - `Content-Type: application/json`
13. Body: Raw JSON with FCM token (from above)
14. Send
15. Should get 201 Created

Done! Your device is registered and will receive notifications.
