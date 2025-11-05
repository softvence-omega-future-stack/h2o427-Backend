# Firebase Push Notifications - Quick API Reference

## Overview

The system automatically sends push notifications for key events:
- User submits background check request → Notify admins
- Admin changes request status → Notify user
- Admin submits report → Notify user

## Setup Summary

1. Get Firebase credentials from https://console.firebase.google.com/
2. Download service account JSON → Save as `firebase-credentials.json`
3. Run: `pip install firebase-admin==6.5.0`
4. Run: `python manage.py makemigrations && python manage.py migrate`
5. Start server: `python manage.py runserver`

## API Endpoints

### Base URL
```
http://127.0.0.1:8000/api/notifications/
```

---

## FCM Device Management

### 1. Register Device Token
**Endpoint:** `POST /api/notifications/fcm-devices/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "registration_token": "eXAMPLE_FCM_TOKEN_FROM_FIREBASE_SDK",
  "device_type": "web"
}
```

**device_type options:**
- `web` - Web browser
- `android` - Android app
- `ios` - iOS app

**Response (201 Created):**
```json
{
  "id": 1,
  "registration_token": "eXAMPLE_FCM_TOKEN_FROM_FIREBASE_SDK",
  "device_type": "web",
  "active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Example (JavaScript):**
```javascript
// Get token from Firebase SDK first
import { messaging, getToken } from './firebase-config';

const fcmToken = await getToken(messaging, { vapidKey: 'YOUR_VAPID_KEY' });

// Register with backend
const response = await fetch('http://127.0.0.1:8000/api/notifications/fcm-devices/', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    registration_token: fcmToken,
    device_type: 'web'
  })
});
```

---

### 2. List User's Devices
**Endpoint:** `GET /api/notifications/fcm-devices/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "registration_token": "token_1",
    "device_type": "web",
    "active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": 2,
    "registration_token": "token_2",
    "device_type": "android",
    "active": true,
    "created_at": "2024-01-14T08:20:00Z",
    "updated_at": "2024-01-14T08:20:00Z"
  }
]
```

---

### 3. Delete Device Token
**Endpoint:** `DELETE /api/notifications/fcm-devices/{id}/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response (204 No Content)**

---

### 4. Deactivate All Devices
**Endpoint:** `POST /api/notifications/fcm-devices/deactivate-all/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully deactivated 3 devices",
  "count": 3
}
```

---

## Notification Management

### 5. List Notifications
**Endpoint:** `GET /api/notifications/notifications/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Query Parameters:**
- `is_read=true/false` - Filter by read status
- `type=admin_to_user` or `user_to_admin` or `system` - Filter by type
- `category=background_check` or `subscription` or `payment` or `report` or `general`

**Examples:**
```
GET /api/notifications/notifications/?is_read=false
GET /api/notifications/notifications/?type=admin_to_user
GET /api/notifications/notifications/?category=background_check
GET /api/notifications/notifications/?is_read=false&category=report
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "recipient": 5,
    "recipient_details": {
      "id": 5,
      "username": "johndoe",
      "email": "john@example.com",
      "full_name": "John Doe"
    },
    "sender": null,
    "sender_details": null,
    "type": "system",
    "type_display": "System",
    "category": "background_check",
    "category_display": "Background Check",
    "title": "Background Check Request Received",
    "message": "Your background check request has been received and is being processed.",
    "is_read": false,
    "read_at": null,
    "related_object_type": "Request",
    "related_object_id": 10,
    "action_url": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  }
]
```

---

### 6. Get Unread Count
**Endpoint:** `GET /api/notifications/notifications/unread-count/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response (200 OK):**
```json
{
  "unread_count": 5
}
```

**Example (JavaScript):**
```javascript
const response = await fetch('http://127.0.0.1:8000/api/notifications/notifications/unread-count/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});

const { unread_count } = await response.json();
console.log(`You have ${unread_count} unread notifications`);
```

---

### 7. Mark Notifications as Read
**Endpoint:** `POST /api/notifications/notifications/mark-read/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
```

**Request Body (mark specific notifications):**
```json
{
  "notification_ids": [1, 2, 3],
  "is_read": true
}
```

**Request Body (mark all notifications):**
```json
{
  "is_read": true
}
```

**Response (200 OK):**
```json
{
  "message": "Successfully marked 3 notifications as read",
  "count": 3
}
```

---

### 8. Mark All as Read
**Endpoint:** `POST /api/notifications/notifications/mark-all-read/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully marked 5 notifications as read",
  "count": 5
}
```

---

### 9. Clear Read Notifications
**Endpoint:** `DELETE /api/notifications/notifications/clear-read/`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully deleted 10 read notifications",
  "count": 10
}
```

---

## Automatic Notification Events

### Event 1: User Submits Background Check Request

**Trigger:** User creates new background check request

**Notifications Sent:**
1. **To User (confirmation):**
   - Type: `system`
   - Category: `background_check`
   - Title: "Background Check Request Received"
   - Message: "Your request has been received and is being processed."

2. **To All Admins:**
   - Type: `user_to_admin`
   - Category: `background_check`
   - Title: "New Background Check Request"
   - Message: "{User} has submitted a new background check request."

**Push Notification:** ✅ Sent to all admin devices

---

### Event 2: Admin Changes Request Status

**Trigger:** Admin updates request status (Pending → In Progress → Completed)

**Notifications Sent:**
1. **To User:**
   - Type: `admin_to_user`
   - Category: `background_check`
   - Title: "Background Check Status: {status}"
   - Message: Status-specific message

**Status Messages:**
- `Pending`: "Your background check request is pending review."
- `In Progress`: "Your background check is now in progress."
- `Completed`: "Your background check has been completed!"

**Push Notification:** ✅ Sent to user's devices

---

### Event 3: Admin Submits Report

**Trigger:** Admin completes background check report

**Notifications Sent:**
1. **To User:**
   - Type: `admin_to_user`
   - Category: `report`
   - Title: "Background Check Report Ready"
   - Message: "Your background check report is now available for download."

**Push Notification:** ✅ Sent to user's devices

---

## Frontend Integration Examples

### React Hook for Notifications

```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

const useNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  const API_BASE = 'http://127.0.0.1:8000/api/notifications';
  const token = localStorage.getItem('accessToken');

  const headers = {
    Authorization: `Bearer ${token}`
  };

  // Fetch notifications
  const fetchNotifications = async (filters = {}) => {
    try {
      const params = new URLSearchParams(filters);
      const response = await axios.get(
        `${API_BASE}/notifications/?${params}`,
        { headers }
      );
      setNotifications(response.data);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  // Fetch unread count
  const fetchUnreadCount = async () => {
    try {
      const response = await axios.get(
        `${API_BASE}/notifications/unread-count/`,
        { headers }
      );
      setUnreadCount(response.data.unread_count);
    } catch (error) {
      console.error('Error fetching unread count:', error);
    }
  };

  // Mark as read
  const markAsRead = async (notificationIds) => {
    try {
      await axios.post(
        `${API_BASE}/notifications/mark-read/`,
        { notification_ids: notificationIds, is_read: true },
        { headers }
      );
      
      // Refresh data
      await fetchNotifications();
      await fetchUnreadCount();
    } catch (error) {
      console.error('Error marking as read:', error);
    }
  };

  // Mark all as read
  const markAllAsRead = async () => {
    try {
      await axios.post(
        `${API_BASE}/notifications/mark-all-read/`,
        {},
        { headers }
      );
      
      // Refresh data
      await fetchNotifications();
      await fetchUnreadCount();
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  // Register FCM token
  const registerDevice = async (fcmToken, deviceType = 'web') => {
    try {
      await axios.post(
        `${API_BASE}/fcm-devices/`,
        { registration_token: fcmToken, device_type: deviceType },
        { headers }
      );
      console.log('Device registered for push notifications');
    } catch (error) {
      console.error('Error registering device:', error);
    }
  };

  // Initial fetch
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await fetchNotifications();
      await fetchUnreadCount();
      setLoading(false);
    };

    loadData();

    // Poll for new notifications every 30 seconds
    const interval = setInterval(() => {
      fetchUnreadCount();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  return {
    notifications,
    unreadCount,
    loading,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    registerDevice
  };
};

export default useNotifications;
```

### Notification Badge Component

```javascript
import { Badge } from './Badge';
import useNotifications from './hooks/useNotifications';

const NotificationBadge = () => {
  const { unreadCount } = useNotifications();

  return (
    <div className="relative">
      <button className="notification-icon">
        🔔
        {unreadCount > 0 && (
          <Badge className="absolute -top-1 -right-1">
            {unreadCount > 99 ? '99+' : unreadCount}
          </Badge>
        )}
      </button>
    </div>
  );
};
```

### Notification List Component

```javascript
import useNotifications from './hooks/useNotifications';

const NotificationList = () => {
  const {
    notifications,
    loading,
    markAsRead,
    markAllAsRead
  } = useNotifications();

  if (loading) return <div>Loading...</div>;

  return (
    <div className="notification-list">
      <div className="flex justify-between p-4">
        <h2>Notifications</h2>
        <button onClick={markAllAsRead}>
          Mark all as read
        </button>
      </div>

      {notifications.map(notification => (
        <div
          key={notification.id}
          className={`notification-item ${!notification.is_read ? 'unread' : ''}`}
          onClick={() => markAsRead([notification.id])}
        >
          <div className="notification-header">
            <span className="notification-title">{notification.title}</span>
            <span className="notification-time">
              {new Date(notification.created_at).toLocaleString()}
            </span>
          </div>
          <p className="notification-message">{notification.message}</p>
          <div className="notification-meta">
            <span className="badge">{notification.category_display}</span>
            {!notification.is_read && <span className="badge unread">Unread</span>}
          </div>
        </div>
      ))}

      {notifications.length === 0 && (
        <div className="text-center p-8 text-gray-500">
          No notifications
        </div>
      )}
    </div>
  );
};
```

---

## Testing

### Test Device Registration

```bash
curl -X POST http://127.0.0.1:8000/api/notifications/fcm-devices/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "registration_token": "test_token_123",
    "device_type": "web"
  }'
```

### Test Get Unread Count

```bash
curl -X GET http://127.0.0.1:8000/api/notifications/notifications/unread-count/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Test Mark as Read

```bash
curl -X POST http://127.0.0.1:8000/api/notifications/notifications/mark-read/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_ids": [1, 2],
    "is_read": true
  }'
```

---

## Database Schema

### FCMDevice Model
```python
- id: Integer (Primary Key)
- user: ForeignKey to User
- registration_token: CharField (unique)
- device_type: CharField (choices: web, android, ios)
- active: Boolean (default: True)
- created_at: DateTime
- updated_at: DateTime
```

### Notification Model
```python
- id: Integer (Primary Key)
- recipient: ForeignKey to User
- sender: ForeignKey to User (nullable)
- type: CharField (choices: admin_to_user, user_to_admin, system)
- category: CharField (choices: background_check, subscription, payment, report, general)
- title: CharField
- message: TextField
- is_read: Boolean
- read_at: DateTime (nullable)
- push_sent: Boolean (default: False)
- push_sent_at: DateTime (nullable)
- push_error: TextField (nullable)
- related_object_type: CharField
- related_object_id: Integer
- action_url: CharField
- created_at: DateTime
- updated_at: DateTime
```

---

## Quick Troubleshooting

**No notifications received:**
1. Check device is registered: `GET /api/notifications/fcm-devices/`
2. Check notification exists: `GET /api/notifications/notifications/`
3. Check push_sent status in database
4. Verify Firebase credentials are correct

**Permission denied:**
1. Check JWT token is valid
2. Ensure user is authenticated
3. Verify Authorization header format: `Bearer <token>`

**Firebase errors:**
1. Check `firebase-credentials.json` exists
2. Verify FIREBASE_CREDENTIALS_PATH in settings
3. Run migrations: `python manage.py migrate`

---

## Complete Workflow Example

### Frontend Flow:

```javascript
// 1. Initialize Firebase (on app load)
import { messaging, getToken } from './firebase-config';

// 2. Request notification permission
const permission = await Notification.requestPermission();

if (permission === 'granted') {
  // 3. Get FCM token
  const fcmToken = await getToken(messaging, { vapidKey: VAPID_KEY });
  
  // 4. Register with backend
  await fetch('http://127.0.0.1:8000/api/notifications/fcm-devices/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      registration_token: fcmToken,
      device_type: 'web'
    })
  });
  
  // 5. Listen for messages
  onMessage(messaging, (payload) => {
    console.log('Notification received:', payload);
    // Show notification UI
  });
  
  // 6. Fetch existing notifications
  const response = await fetch('http://127.0.0.1:8000/api/notifications/notifications/', {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  const notifications = await response.json();
  
  // 7. Get unread count
  const countResponse = await fetch('http://127.0.0.1:8000/api/notifications/notifications/unread-count/', {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  });
  const { unread_count } = await countResponse.json();
}
```

---

## Support Files

- Full Setup Guide: `FIREBASE_SETUP_GUIDE.md`
- Firebase Service: `notifications/firebase_service.py`
- Signal Handlers: `notifications/signals.py`
- Models: `notifications/models.py`
- Serializers: `notifications/serializers.py`
- Views: `notifications/views.py`
