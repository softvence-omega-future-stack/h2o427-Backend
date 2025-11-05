# 🚀 Quick Start: Firebase Push Notifications

## 5-Minute Setup Guide

### Prerequisites
- ✅ firebase-admin installed (`pip install firebase-admin==6.5.0`)
- ✅ Migrations applied (`python manage.py migrate`)
- ✅ Server running (`python manage.py runserver`)

---

## Step 1: Get Firebase Credentials (2 minutes)

1. **Go to Firebase Console**
   ```
   https://console.firebase.google.com/
   ```

2. **Create/Select Project**
   - Click "Add project" or select existing
   - Name: "Background Check App"

3. **Get Service Account Key**
   - Click gear icon ⚙️ → "Project settings"
   - Go to "Service accounts" tab
   - Click "Generate new private key"
   - Download the JSON file

4. **Save Credentials**
   ```
   Save as: firebase-credentials.json
   Location: c:\Users\anower\Desktop\All Project\h20427\h2o427-Backend\
   ```

---

## Step 2: Test Backend (1 minute)

```bash
# Test Firebase initialization
python manage.py shell

>>> from notifications.firebase_service import initialize_firebase
>>> initialize_firebase()
# Should see: "Firebase Admin SDK initialized successfully"

>>> exit()
```

---

## Step 3: Test Device Registration (30 seconds)

```bash
# Using curl (Windows PowerShell)
$headers = @{
    "Authorization" = "Bearer YOUR_JWT_TOKEN"
    "Content-Type" = "application/json"
}

$body = @{
    registration_token = "test_token_123"
    device_type = "web"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/notifications/fcm-devices/" -Method POST -Headers $headers -Body $body
```

---

## Step 4: Get Frontend Credentials (1 minute)

1. **In Firebase Console**
   - Project Settings → General
   - Scroll to "Your apps"
   - Click Web icon (</>) or "Add app"
   - Register app name: "Background Check Web"

2. **Copy Config**
   ```javascript
   const firebaseConfig = {
     apiKey: "AIza...",
     authDomain: "your-app.firebaseapp.com",
     projectId: "your-project-id",
     storageBucket: "your-app.appspot.com",
     messagingSenderId: "123456789",
     appId: "1:123456789:web:abc123"
   };
   ```

3. **Get VAPID Key**
   - Project Settings → Cloud Messaging
   - Scroll to "Web Push certificates"
   - Click "Generate key pair"
   - Copy the key

---

## Step 5: Frontend Code (30 seconds)

### Quick Integration (React)

```javascript
// firebase-config.js
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

const firebaseConfig = {
  // Paste your config here
};

const app = initializeApp(firebaseConfig);
const messaging = getMessaging(app);

export { messaging, getToken, onMessage };
```

```javascript
// App.js or useEffect
import { messaging, getToken, onMessage } from './firebase-config';

const VAPID_KEY = 'YOUR_VAPID_KEY';

// Request permission and register
const permission = await Notification.requestPermission();
if (permission === 'granted') {
  const token = await getToken(messaging, { vapidKey: VAPID_KEY });
  
  // Register with backend
  await fetch('http://127.0.0.1:8000/api/notifications/fcm-devices/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${yourJWTToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      registration_token: token,
      device_type: 'web'
    })
  });
}

// Listen for messages
onMessage(messaging, (payload) => {
  console.log('Notification:', payload);
  alert(`${payload.notification.title}: ${payload.notification.body}`);
});
```

---

## Testing the Flow

### Test 1: Submit Request (User → Admin)
```bash
# User submits background check request
POST /api/requests/api/
```
**Expected:** Admin receives push notification "New Background Check Request"

### Test 2: Update Status (Admin → User)
```bash
# Admin changes status to "In Progress"
PUT /api/requests/api/{id}/
```
**Expected:** User receives push notification "Background Check Status: In Progress"

### Test 3: Complete Report (Admin → User)
```bash
# Admin submits report
POST /api/requests/api/{id}/submit-report/
```
**Expected:** User receives push notification "Background Check Report Ready"

---

## API Quick Reference

### Register Device
```bash
POST /api/notifications/fcm-devices/
{
  "registration_token": "FCM_TOKEN_FROM_FIREBASE",
  "device_type": "web"  # or "android", "ios"
}
```

### Get Unread Count
```bash
GET /api/notifications/notifications/unread-count/
```

### List Notifications
```bash
GET /api/notifications/notifications/?is_read=false
```

### Mark as Read
```bash
POST /api/notifications/notifications/mark-read/
{
  "notification_ids": [1, 2, 3],
  "is_read": true
}
```

---

## Automatic Notifications

The system automatically sends notifications for:

| Event | Recipient | Type | Push? |
|-------|-----------|------|-------|
| User submits request | All admins | user_to_admin | ✅ |
| User submits request | User (confirm) | system | ✅ |
| Admin changes status | User | admin_to_user | ✅ |
| Admin submits report | User | admin_to_user | ✅ |
| Report generated | User | admin_to_user | ✅ |

---

## Troubleshooting

### Backend Issues

**"Could not load credentials"**
```bash
# Check file exists
ls firebase-credentials.json

# Check path in settings
python manage.py shell
>>> from django.conf import settings
>>> print(settings.FIREBASE_CREDENTIALS_PATH)
```

**"Import Error: firebase_admin"**
```bash
pip install firebase-admin==6.5.0
```

### Frontend Issues

**"Permission denied"**
- Check browser notification settings
- Ensure HTTPS (required for service workers)
- Try incognito/private mode

**"Token not generating"**
- Verify VAPID key is correct
- Check Firebase config is correct
- Ensure service worker is registered

---

## Production Deployment

### Render.com

1. **Upload credentials as secret file**
   - Dashboard → Your Service → Environment
   - Add Secret File: `firebase-credentials.json`
   - Upload your JSON file

2. **Set environment variable**
   ```
   FIREBASE_CREDENTIALS_PATH=/etc/secrets/firebase-credentials.json
   ```

3. **Deploy**
   - Render will automatically install firebase-admin
   - Migrations will run automatically

---

## Complete Documentation

- **Setup Guide**: `FIREBASE_SETUP_GUIDE.md` (detailed setup)
- **API Reference**: `NOTIFICATION_API_REFERENCE.md` (all endpoints)
- **Implementation**: `FIREBASE_IMPLEMENTATION_SUMMARY.md` (what was built)

---

## Support

**Questions?**
1. Check `FIREBASE_SETUP_GUIDE.md` for detailed instructions
2. Review `NOTIFICATION_API_REFERENCE.md` for API examples
3. Test with curl commands provided above

**Firebase Resources:**
- Console: https://console.firebase.google.com/
- Docs: https://firebase.google.com/docs/cloud-messaging
- JS Client: https://firebase.google.com/docs/cloud-messaging/js/client

---

## You're Done! 🎉

Once you have `firebase-credentials.json` in place:
1. Backend automatically sends push notifications ✅
2. Frontend just needs to register device tokens ✅
3. All notification logic is handled automatically ✅

**Next:** Get your firebase-credentials.json and test the notifications!
