# Firebase Cloud Messaging (FCM) Setup Guide

This guide will help you set up Firebase Cloud Messaging for push notifications in your application.

## Table of Contents
1. [Backend Setup](#backend-setup)
2. [Frontend Setup](#frontend-setup)
3. [Testing](#testing)
4. [Troubleshooting](#troubleshooting)

---

## Backend Setup

### Step 1: Create Firebase Project

1. **Go to Firebase Console**
   - Visit: https://console.firebase.google.com/
   - Click "Add project" or select existing project

2. **Create/Select Project**
   - Enter project name: `Background Check App`
   - Accept Firebase terms
   - Click "Continue"

3. **Enable Google Analytics** (Optional)
   - Choose default account or create new one
   - Click "Create project"

### Step 2: Enable Cloud Messaging

1. **Go to Project Settings**
   - Click the gear icon ⚙️ next to "Project Overview"
   - Select "Project settings"

2. **Go to Cloud Messaging Tab**
   - Click on "Cloud Messaging" tab
   - If prompted, enable "Cloud Messaging API (Legacy)"

3. **Note Your Credentials** (for frontend)
   - **Server Key**: Found under "Cloud Messaging API (Legacy)"
   - **Sender ID**: Found under "Cloud Messaging API (Legacy)"

### Step 3: Generate Service Account Key

1. **Go to Service Accounts**
   - In Project Settings, click "Service accounts" tab
   - Click "Generate new private key"
   - A dialog will appear warning you to keep this key secret
   - Click "Generate key"

2. **Download JSON File**
   - Save the downloaded JSON file securely
   - Rename it to `firebase-credentials.json`

3. **Place in Project Root**
   ```bash
   # Move the file to your project root
   # Should be at: c:\Users\anower\Desktop\All Project\h20427\h2o427-Backend\firebase-credentials.json
   ```

4. **Add to .gitignore**
   ```bash
   # Add this line to .gitignore
   firebase-credentials.json
   ```

### Step 4: Install Dependencies

```bash
# Install firebase-admin
pip install firebase-admin==6.5.0
```

### Step 5: Configure Environment Variables

Add to your `.env` file:

```env
# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
```

For production (Render.com):
- Upload `firebase-credentials.json` as a secret file
- Set `FIREBASE_CREDENTIALS_PATH` to the uploaded file path

### Step 6: Run Migrations

```bash
# Create and apply migrations for new FCMDevice model
python manage.py makemigrations notifications
python manage.py migrate notifications
```

### Step 7: Verify Backend Setup

```bash
# Test Python import
python -c "import firebase_admin; print('Firebase Admin SDK installed successfully')"

# Check if credentials file exists
ls firebase-credentials.json
```

---

## Frontend Setup

### For Web Application (React/Next.js)

#### Step 1: Add Firebase to Your Project

1. **Install Firebase SDK**
   ```bash
   npm install firebase
   # or
   yarn add firebase
   ```

2. **Get Web App Config**
   - Go to Firebase Console
   - Click "Project Settings" ⚙️
   - Scroll to "Your apps"
   - Click "Web" icon (</>) or "Add app"
   - Register your app
   - Copy the `firebaseConfig` object

#### Step 2: Initialize Firebase

Create `firebase-config.js`:

```javascript
import { initializeApp } from 'firebase/app';
import { getMessaging, getToken, onMessage } from 'firebase/messaging';

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase Cloud Messaging
const messaging = getMessaging(app);

export { messaging, getToken, onMessage };
```

#### Step 3: Create Service Worker

Create `public/firebase-messaging-sw.js`:

```javascript
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

// Your Firebase configuration
firebase.initializeApp({
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
  console.log('Background Message:', payload);
  
  const notificationTitle = payload.notification.title;
  const notificationOptions = {
    body: payload.notification.body,
    icon: '/icon-192x192.png',
    badge: '/badge-72x72.png',
    data: payload.data
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  // Navigate to the URL if provided
  if (event.notification.data && event.notification.data.action_url) {
    event.waitUntil(
      clients.openWindow(event.notification.data.action_url)
    );
  }
});
```

#### Step 4: Get VAPID Key

1. Go to Firebase Console
2. Project Settings → Cloud Messaging
3. Scroll to "Web Push certificates"
4. Click "Generate key pair"
5. Copy the generated key

#### Step 5: Request Permission and Get Token

Create `hooks/useNotifications.js`:

```javascript
import { useState, useEffect } from 'react';
import { messaging, getToken, onMessage } from '../firebase-config';
import axios from 'axios';

const VAPID_KEY = 'YOUR_VAPID_KEY'; // From Firebase Console

export const useNotifications = () => {
  const [permission, setPermission] = useState(Notification.permission);
  const [token, setToken] = useState(null);

  useEffect(() => {
    // Request permission and get token
    const requestPermission = async () => {
      try {
        const permission = await Notification.requestPermission();
        setPermission(permission);

        if (permission === 'granted') {
          const currentToken = await getToken(messaging, {
            vapidKey: VAPID_KEY
          });

          if (currentToken) {
            setToken(currentToken);
            
            // Register token with backend
            await registerDeviceToken(currentToken);
          } else {
            console.log('No registration token available.');
          }
        }
      } catch (error) {
        console.error('Error getting permission/token:', error);
      }
    };

    requestPermission();

    // Listen for foreground messages
    const unsubscribe = onMessage(messaging, (payload) => {
      console.log('Foreground message:', payload);
      
      // Show notification
      new Notification(payload.notification.title, {
        body: payload.notification.body,
        icon: '/icon-192x192.png',
        data: payload.data
      });
    });

    return () => unsubscribe();
  }, []);

  const registerDeviceToken = async (token) => {
    try {
      const authToken = localStorage.getItem('accessToken'); // Your JWT token
      
      await axios.post(
        'http://127.0.0.1:8000/api/notifications/fcm-devices/',
        {
          registration_token: token,
          device_type: 'web'
        },
        {
          headers: {
            Authorization: `Bearer ${authToken}`
          }
        }
      );
      
      console.log('Device token registered successfully');
    } catch (error) {
      console.error('Failed to register device token:', error);
    }
  };

  return { permission, token };
};
```

#### Step 6: Use in Your Components

```javascript
import { useNotifications } from './hooks/useNotifications';

function App() {
  const { permission, token } = useNotifications();

  return (
    <div>
      <h1>My App</h1>
      
      {permission === 'denied' && (
        <div className="alert alert-warning">
          Please enable notifications in your browser settings
        </div>
      )}
      
      {permission === 'granted' && token && (
        <div className="alert alert-success">
          Notifications enabled ✓
        </div>
      )}
    </div>
  );
}
```

### For Mobile Apps (React Native)

#### Step 1: Install Dependencies

```bash
npm install @react-native-firebase/app @react-native-firebase/messaging
# or
yarn add @react-native-firebase/app @react-native-firebase/messaging
```

#### Step 2: Configure Android

1. **Download google-services.json**
   - Firebase Console → Project Settings
   - Under "Your apps", select Android app
   - Download `google-services.json`
   - Place in `android/app/` directory

2. **Update android/build.gradle**
   ```gradle
   buildscript {
     dependencies {
       classpath 'com.google.gms:google-services:4.3.15'
     }
   }
   ```

3. **Update android/app/build.gradle**
   ```gradle
   apply plugin: 'com.google.gms.google-services'
   ```

#### Step 3: Configure iOS

1. **Download GoogleService-Info.plist**
   - Firebase Console → Project Settings
   - Under "Your apps", select iOS app
   - Download `GoogleService-Info.plist`
   - Add to Xcode project

2. **Enable Push Notifications**
   - Open Xcode
   - Go to Signing & Capabilities
   - Click "+ Capability"
   - Add "Push Notifications"
   - Add "Background Modes" → Check "Remote notifications"

#### Step 4: Request Permission and Register Token

```javascript
import messaging from '@react-native-firebase/messaging';
import axios from 'axios';

// Request permission
async function requestUserPermission() {
  const authStatus = await messaging().requestPermission();
  const enabled =
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;

  if (enabled) {
    console.log('Authorization status:', authStatus);
    
    // Get FCM token
    const token = await messaging().getToken();
    console.log('FCM Token:', token);
    
    // Register with backend
    await registerDeviceToken(token, 'android'); // or 'ios'
  }
}

async function registerDeviceToken(token, deviceType) {
  try {
    const authToken = await AsyncStorage.getItem('accessToken');
    
    await axios.post(
      'http://127.0.0.1:8000/api/notifications/fcm-devices/',
      {
        registration_token: token,
        device_type: deviceType
      },
      {
        headers: {
          Authorization: `Bearer ${authToken}`
        }
      }
    );
    
    console.log('Device token registered');
  } catch (error) {
    console.error('Failed to register token:', error);
  }
}

// Listen for messages
useEffect(() => {
  // Foreground message handler
  const unsubscribe = messaging().onMessage(async remoteMessage => {
    console.log('Foreground message:', remoteMessage);
  });

  // Background message handler
  messaging().setBackgroundMessageHandler(async remoteMessage => {
    console.log('Background message:', remoteMessage);
  });

  return unsubscribe;
}, []);

// Call on app start
requestUserPermission();
```

---

## Testing

### Test Backend FCM Integration

```bash
# 1. Create migrations
python manage.py makemigrations
python manage.py migrate

# 2. Run server
python manage.py runserver

# 3. Test Firebase initialization
python manage.py shell
>>> from notifications.firebase_service import initialize_firebase
>>> initialize_firebase()
>>> # Should see: "Firebase Admin SDK initialized successfully"
```

### Test Device Registration

```bash
# Register a device token (using curl or Postman)
curl -X POST http://127.0.0.1:8000/api/notifications/fcm-devices/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "registration_token": "YOUR_DEVICE_TOKEN",
    "device_type": "web"
  }'
```

### Test Push Notification

```bash
# Send test notification via Django shell
python manage.py shell

from authentication.models import User
from notifications.firebase_service import send_notification_to_user

user = User.objects.first()
result = send_notification_to_user(
    user,
    "Test Notification",
    "This is a test push notification",
    notification_type="general"
)

print(result)
# Should see: {'success_count': 1, 'failure_count': 0, 'failed_tokens': []}
```

### Test Automatic Notifications

```bash
# Create a background check request
curl -X POST http://127.0.0.1:8000/api/requests/api/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "date_of_birth": "1990-01-01",
    ...
  }'

# Check if admin received notification
# Check admin's notification list
```

---

## API Endpoints

### FCM Device Management

#### Register Device Token
```http
POST /api/notifications/fcm-devices/
Authorization: Bearer <token>
Content-Type: application/json

{
  "registration_token": "device_fcm_token_here",
  "device_type": "web"  // or "android" or "ios"
}
```

#### List User's Devices
```http
GET /api/notifications/fcm-devices/
Authorization: Bearer <token>
```

#### Delete Device Token
```http
DELETE /api/notifications/fcm-devices/{id}/
Authorization: Bearer <token>
```

#### Deactivate All Devices
```http
POST /api/notifications/fcm-devices/deactivate-all/
Authorization: Bearer <token>
```

### Notifications

#### List Notifications
```http
GET /api/notifications/notifications/
Authorization: Bearer <token>

Query Parameters:
- is_read=true/false
- type=admin_to_user/user_to_admin/system
- category=background_check/subscription/payment/report/general
```

#### Get Unread Count
```http
GET /api/notifications/notifications/unread-count/
Authorization: Bearer <token>
```

#### Mark as Read
```http
POST /api/notifications/notifications/mark-read/
Authorization: Bearer <token>
Content-Type: application/json

{
  "notification_ids": [1, 2, 3],  // Optional, omit to mark all
  "is_read": true
}
```

#### Mark All as Read
```http
POST /api/notifications/notifications/mark-all-read/
Authorization: Bearer <token>
```

---

## Notification Triggers

The system automatically sends notifications for these events:

### User Actions → Notify Admins

1. **User submits background check request**
   - Notification Type: `user_to_admin`
   - Category: `background_check`
   - Sent to: All admin users

### Admin Actions → Notify User

1. **Admin changes request status**
   - Notification Type: `admin_to_user`
   - Category: `background_check`
   - Sent to: Request owner

2. **Admin submits report**
   - Notification Type: `admin_to_user`
   - Category: `report`
   - Sent to: Request owner

3. **Report generated**
   - Notification Type: `admin_to_user`
   - Category: `report`
   - Sent to: Request owner

### System Notifications

1. **Request received confirmation**
   - Notification Type: `system`
   - Category: `background_check`
   - Sent to: Request creator

---

## Troubleshooting

### Firebase Admin SDK Issues

**Error: Could not load credentials**
```bash
# Check if file exists
ls firebase-credentials.json

# Check file permissions
chmod 600 firebase-credentials.json

# Verify path in settings.py
python manage.py shell
>>> from django.conf import settings
>>> print(settings.FIREBASE_CREDENTIALS_PATH)
```

**Error: Firebase app already initialized**
- This is normal if you're running commands multiple times
- The SDK checks and only initializes once

### Frontend Issues

**Service worker not registering**
```javascript
// Check browser console
navigator.serviceWorker.getRegistrations().then(registrations => {
  console.log('Service Workers:', registrations);
});

// Force update
navigator.serviceWorker.getRegistrations().then(registrations => {
  registrations.forEach(reg => reg.update());
});
```

**Permission denied**
- Check browser notification settings
- Chrome: `chrome://settings/content/notifications`
- Firefox: `about:preferences#privacy`

**Token not generating**
- Ensure HTTPS (required for service workers)
- Check VAPID key is correct
- Verify Firebase config is correct

### Push Notification Not Received

1. **Check device is registered**
   ```bash
   # In Django shell
   from notifications.models import FCMDevice
   FCMDevice.objects.filter(user=user)
   ```

2. **Check notification was created**
   ```bash
   from notifications.models import Notification
   Notification.objects.filter(recipient=user).order_by('-created_at')[:5]
   ```

3. **Check push_sent status**
   ```bash
   notification = Notification.objects.latest('created_at')
   print(f"Push sent: {notification.push_sent}")
   print(f"Push error: {notification.push_error}")
   ```

4. **Test Firebase connection**
   ```bash
   python manage.py shell
   from notifications.firebase_service import send_push_notification
   result = send_push_notification(['test_token'], 'Test', 'Testing')
   print(result)
   ```

### Common Errors

**Import Error: firebase_admin**
```bash
pip install firebase-admin==6.5.0
```

**Migration Error**
```bash
python manage.py makemigrations notifications
python manage.py migrate notifications
```

**Invalid Token**
- Token expired or invalid
- Device uninstalled app
- Token deactivated automatically

---

## Production Deployment

### Render.com

1. **Upload Credentials**
   - Go to Render Dashboard
   - Select your service
   - Go to "Environment" tab
   - Add secret file: `firebase-credentials.json`
   - Upload your credentials file

2. **Set Environment Variable**
   ```
   FIREBASE_CREDENTIALS_PATH=/etc/secrets/firebase-credentials.json
   ```

### Docker

Add to Dockerfile:
```dockerfile
# Copy Firebase credentials
COPY firebase-credentials.json /app/firebase-credentials.json

# Set environment variable
ENV FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
```

Add to `.dockerignore` for security:
```
firebase-credentials.json
```

---

## Security Best Practices

1. **Never commit credentials to Git**
   ```bash
   # Add to .gitignore
   firebase-credentials.json
   .env
   ```

2. **Use environment variables**
   - Store path in .env file
   - Use different credentials for dev/prod

3. **Restrict API access**
   - Use Firebase security rules
   - Validate tokens on backend

4. **Rotate keys regularly**
   - Generate new service account keys periodically
   - Revoke old keys

---

## Next Steps

1. ✅ Install firebase-admin package
2. ✅ Create Firebase project
3. ✅ Download service account key
4. ✅ Place credentials file in project root
5. ✅ Run migrations
6. ✅ Configure frontend
7. ✅ Test device registration
8. ✅ Test push notifications
9. ✅ Deploy to production

---

## Support

For issues or questions:
- Firebase Documentation: https://firebase.google.com/docs/cloud-messaging
- FCM Client Setup: https://firebase.google.com/docs/cloud-messaging/js/client
- Backend Code: `notifications/firebase_service.py`
- Frontend Example: See this guide above
