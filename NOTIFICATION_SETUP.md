# Notification System Setup Guide

## Quick Setup Steps

### 1. Activate Virtual Environment (if you have one)
```powershell
# If you have a virtual environment, activate it first
# Example:
# .venv\Scripts\Activate.ps1
```

### 2. Install Dependencies (if needed)
```powershell
pip install django djangorestframework djangorestframework-simplejwt drf-yasg django-filter
```

### 3. Run Migrations
```powershell
# Create migration files
python manage.py makemigrations notifications

# Apply migrations to database
python manage.py migrate notifications

# Or migrate all apps
python manage.py migrate
```

### 4. Create Superuser (if you don't have one)
```powershell
python manage.py createsuperuser
```

### 5. Test the System
```powershell
# Run the test script
python test_notifications.py

# Or via Django shell
python manage.py shell
# Then run:
# exec(open('test_notifications.py').read())
```

### 6. Start the Server
```powershell
python manage.py runserver
```

### 7. Access the System

**Admin Interface:**
- URL: http://localhost:8000/admin/notifications/notification/
- Login with your superuser credentials

**API Documentation:**
- Swagger UI: http://localhost:8000/swagger/
- API Endpoints: http://localhost:8000/api/notifications/

**Test API Endpoints:**
```powershell
# Get your auth token first
curl -X POST http://localhost:8000/api/auth/login/ -H "Content-Type: application/json" -d "{\"email\":\"your@email.com\",\"password\":\"yourpassword\"}"

# Then use the token to access notifications
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/notifications/
```

## API Endpoints Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notifications/` | GET | List all notifications |
| `/api/notifications/` | POST | Create a notification |
| `/api/notifications/{id}/` | GET | Get notification details |
| `/api/notifications/{id}/` | PATCH/PUT | Update notification |
| `/api/notifications/{id}/` | DELETE | Delete notification |
| `/api/notifications/bulk-create/` | POST | Create bulk notifications (admin) |
| `/api/notifications/unread-count/` | GET | Get unread count |
| `/api/notifications/mark-read/` | POST | Mark as read/unread |
| `/api/notifications/mark-all-read/` | POST | Mark all as read |
| `/api/notifications/clear-read/` | DELETE | Delete all read notifications |

## Troubleshooting

### Django Not Found
```powershell
# Make sure you're in the correct directory
cd "C:\Users\anower\Desktop\All Project\h20427\h2o427-Backend"

# Install Django
pip install django
```

### Migration Issues
```powershell
# If you get migration conflicts, try:
python manage.py migrate --run-syncdb

# Or reset migrations (WARNING: This will delete data)
# python manage.py migrate notifications zero
# python manage.py makemigrations notifications
# python manage.py migrate notifications
```

### Import Errors
```powershell
# Make sure all dependencies are installed
pip install -r requirements.txt
```

## What Was Implemented

✅ **Notification Model** - Complete database model with all fields
✅ **API Views** - RESTful API with ViewSet
✅ **Serializers** - For data validation and transformation
✅ **Admin Interface** - Beautiful admin panel with filters and actions
✅ **Signal Handlers** - Automatic notifications for events
✅ **URLs** - All routes configured
✅ **Documentation** - Complete API documentation
✅ **Frontend Component** - React component example
✅ **Test Script** - Comprehensive testing

## Automatic Notifications

The system automatically creates notifications for:
- ✅ New background check requests (User → Admin)
- ✅ Request received confirmation (System → User)
- ✅ Status changes (Admin → User)
- ✅ Report generation (Admin → User)

## Next Steps After Setup

1. **Integrate with Frontend**: Use the `NotificationCenter.jsx` component
2. **Customize Signals**: Edit `notifications/signals.py` for more events
3. **Add WebSockets**: For real-time notifications (optional)
4. **Setup Email/SMS**: For external notifications (optional)

## Support

See `NOTIFICATION_SYSTEM.md` for complete documentation.
