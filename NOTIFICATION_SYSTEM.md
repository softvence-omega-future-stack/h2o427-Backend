# Notification System Documentation

## Overview

This notification system provides bidirectional communication between administrators and users in the H2O427 Background Check system. It automatically generates notifications for important events and allows manual notification creation.

## Features

### 1. **Bidirectional Communication**
- **Admin → User**: Admins can send notifications to users
- **User → Admin**: Users can send notifications to admins
- **System**: Automated system notifications for events

### 2. **Automatic Notifications**

The system automatically creates notifications for:

- ✅ **New background check request submitted** (User → Admin)
- ✅ **Request received confirmation** (System → User)
- ✅ **Status changes** (Pending → In Progress → Completed) (Admin → User)
- ✅ **Report ready for download** (Admin → User)

### 3. **Notification Categories**

- `background_check` - Background check related
- `subscription` - Subscription related
- `payment` - Payment related
- `report` - Report related
- `general` - General notifications

### 4. **Rich Features**

- Mark as read/unread
- Bulk notifications (admin only)
- Unread count
- Related object references
- Action URLs
- Search and filtering
- Admin interface management

## API Endpoints

### Base URL: `/api/notifications/`

### 1. List Notifications
```http
GET /api/notifications/
```

**Query Parameters:**
- `type` - Filter by type (admin_to_user, user_to_admin, system)
- `category` - Filter by category (background_check, subscription, payment, report, general)
- `is_read` - Filter by read status (true/false)
- `search` - Search in title and message
- `ordering` - Sort by field (created_at, is_read)

**Response:**
```json
{
  "count": 10,
  "next": "http://api/notifications/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "recipient": 1,
      "recipient_details": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe"
      },
      "sender": 2,
      "sender_details": {
        "id": 2,
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User"
      },
      "type": "admin_to_user",
      "type_display": "Admin to User",
      "category": "background_check",
      "category_display": "Background Check",
      "title": "Background Check Status: Completed",
      "message": "Your background check has been completed!",
      "is_read": false,
      "read_at": null,
      "related_object_type": "Request",
      "related_object_id": 5,
      "action_url": null,
      "created_at": "2025-10-23T10:30:00Z",
      "updated_at": "2025-10-23T10:30:00Z"
    }
  ]
}
```

### 2. Get Notification Detail
```http
GET /api/notifications/{id}/
```

### 3. Create Notification
```http
POST /api/notifications/
```

**Request Body:**
```json
{
  "recipient": 1,
  "type": "admin_to_user",
  "category": "general",
  "title": "Important Update",
  "message": "Your account has been verified.",
  "related_object_type": "User",
  "related_object_id": 1,
  "action_url": "/profile"
}
```

**Permissions:**
- Admin can create `admin_to_user` or `system` notifications
- Regular users can create `user_to_admin` notifications

### 4. Create Bulk Notifications (Admin Only)
```http
POST /api/notifications/bulk-create/
```

**Request Body:**
```json
{
  "recipient_ids": [1, 2, 3, 4, 5],
  "type": "admin_to_user",
  "category": "general",
  "title": "System Maintenance",
  "message": "The system will be under maintenance on Sunday.",
  "action_url": "/maintenance-schedule"
}
```

### 5. Get Unread Count
```http
GET /api/notifications/unread-count/
```

**Response:**
```json
{
  "unread_count": 5
}
```

### 6. Mark Notifications as Read/Unread
```http
POST /api/notifications/mark-read/
```

**Request Body:**
```json
{
  "notification_ids": [1, 2, 3],
  "is_read": true
}
```

**Note:** If `notification_ids` is omitted, marks all user's notifications.

### 7. Mark All as Read
```http
POST /api/notifications/mark-all-read/
```

### 8. Clear Read Notifications
```http
DELETE /api/notifications/clear-read/
```

Deletes all read notifications for the current user.

### 9. Update Notification
```http
PATCH /api/notifications/{id}/
PUT /api/notifications/{id}/
```

### 10. Delete Notification
```http
DELETE /api/notifications/{id}/
```

## Usage Examples

### Frontend Integration (React/JavaScript)

#### 1. Fetch Notifications
```javascript
const fetchNotifications = async () => {
  const response = await fetch('/api/notifications/', {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  });
  const data = await response.json();
  return data.results;
};
```

#### 2. Get Unread Count
```javascript
const getUnreadCount = async () => {
  const response = await fetch('/api/notifications/unread-count/', {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });
  const data = await response.json();
  return data.unread_count;
};
```

#### 3. Mark as Read
```javascript
const markAsRead = async (notificationId) => {
  await fetch('/api/notifications/mark-read/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      notification_ids: [notificationId],
      is_read: true
    })
  });
};
```

#### 4. Create Notification (User to Admin)
```javascript
const sendToAdmin = async (title, message) => {
  await fetch('/api/notifications/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      recipient: adminUserId, // Get from admin list
      type: 'user_to_admin',
      category: 'general',
      title: title,
      message: message
    })
  });
};
```

#### 5. Send Bulk Notification (Admin Only)
```javascript
const sendBulkNotification = async (userIds, title, message) => {
  await fetch('/api/notifications/bulk-create/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      recipient_ids: userIds,
      type: 'admin_to_user',
      category: 'general',
      title: title,
      message: message
    })
  });
};
```

### Python Usage (Backend)

#### 1. Create Notification Programmatically
```python
from notifications.models import Notification
from authentication.models import User

# Send notification to user
user = User.objects.get(id=1)
Notification.objects.create(
    recipient=user,
    sender=None,  # System notification
    type=Notification.SYSTEM,
    category=Notification.GENERAL,
    title='Welcome!',
    message='Thank you for joining our platform.',
)
```

#### 2. Use Helper Functions
```python
from notifications.signals import send_user_notification, send_admin_notification

# Send to specific user
send_user_notification(
    recipient_user=user,
    title='Payment Received',
    message='Your payment has been processed successfully.',
    category=Notification.PAYMENT,
    sender=admin_user
)

# Send to all admins
send_admin_notification(
    sender_user=user,
    title='Help Request',
    message='User needs assistance with their account.',
    category=Notification.GENERAL
)
```

## Admin Interface

Access the admin interface at: `/admin/notifications/notification/`

### Features:
- View all notifications
- Filter by type, category, read status
- Search by title, message, user
- Mark as read/unread (bulk action)
- Delete notifications
- Color-coded badges for types and categories
- Direct links to related users

## Database Migrations

Run migrations to create the notification tables:

```bash
python manage.py makemigrations notifications
python manage.py migrate notifications
```

## Testing

### Test with cURL

#### Get notifications:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/notifications/
```

#### Create notification:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": 1,
    "type": "admin_to_user",
    "category": "general",
    "title": "Test Notification",
    "message": "This is a test message"
  }' \
  http://localhost:8000/api/notifications/
```

## Customization

### Adding New Notification Types

1. Update `models.py` to add new type choices
2. Update signals in `signals.py` for automatic notifications
3. Update frontend to handle new types

### Adding New Categories

1. Update `CATEGORY_CHOICES` in `models.py`
2. Update color mappings in `admin.py`
3. Update frontend UI accordingly

## Best Practices

1. **Always use signals** for automatic notifications
2. **Use bulk create** for sending to multiple users
3. **Implement polling or WebSockets** for real-time updates in frontend
4. **Mark notifications as read** when user views them
5. **Clean up old notifications** periodically using `clear-read` endpoint
6. **Include action URLs** when appropriate for better UX

## Security Notes

- Only authenticated users can access notification endpoints
- Users can only see their own notifications (unless admin)
- Regular users cannot send `admin_to_user` notifications
- Only admins can create bulk notifications
- Users cannot modify sender field (automatically set)

## Future Enhancements

- [ ] WebSocket support for real-time notifications
- [ ] Email/SMS integration for critical notifications
- [ ] Notification preferences per user
- [ ] Rich text/HTML notifications
- [ ] Notification templates
- [ ] Push notifications for mobile apps
- [ ] Notification scheduling

## Support

For issues or questions, contact the development team.
