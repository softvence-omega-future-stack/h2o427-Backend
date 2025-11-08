# How to Test Notification System Using UI

## Access the Test Page
1. Make sure the Django server is running: `python manage.py runserver`
2. Open your browser and go to: **http://127.0.0.1:8000/api/notifications/test/**

## Step-by-Step Testing Guide

### Step 1: Register a Device Token
This simulates a mobile device or web browser registering for push notifications.

1. **Box 1: Register Device Token**
   - **User ID**: Enter `1` (or any existing user ID from your database)
   - **Device Token**: Enter any test token, for example: `test_device_token_123`
   - **Device Type**: Select `Android`, `iOS`, or `Web`
   - Click **"Register Token"** button

2. **Expected Result**: 
   - You'll see a success message at the top: "Device token registered successfully for User ID: 1"
   - The device will appear in **Box 4** (All Registered Devices)

---

### Step 2: Send a Test Notification
This sends a notification to a specific user.

1. **Box 2: Send Test Notification**
   - **User ID**: Enter `1` (or the user ID you used in Step 1)
   - **Title**: Enter something like `Test Alert`
   - **Message**: Enter `This is a test message to check notifications`
   - **Notification Type**: Select `General` (or any other type)
   - Click **"Send Notification"** button

2. **Expected Result**:
   - Success message appears: "Notification sent successfully to User ID: 1"
   - If the device token is registered, it will also show: "Push sent to X devices"

---

### Step 3: View Notifications
This retrieves all notifications for a specific user.

1. **Box 3: View Notifications**
   - **User ID**: Enter `1` (or the user you sent notification to)
   - Click **"Get Notifications"** button

2. **Expected Result**:
   - The page will reload and show a list of notifications below
   - Each notification shows:
     - ID, Title, Message, Type, Read status, Created time
     - A **"Mark as Read"** button (if not read yet)

---

### Step 4: Mark Notification as Read
After viewing notifications, you can mark them as read.

1. In the notifications list (Box 3), find an unread notification
2. Click the **"Mark as Read"** button next to it

3. **Expected Result**:
   - Success message: "Notification X marked as read"
   - The notification's **Read** status changes to "Yes"
   - The "Mark as Read" button disappears

---

### Step 5: Check All Registered Devices
This shows all devices that have registered for push notifications.

1. **Box 4: All Registered Devices**
   - This box automatically displays all registered devices
   - Shows: User ID, Device Type, Token (truncated), Active status, Registration time

---

## Common Test Scenarios

### Scenario 1: Test End-to-End Flow
1. Register a device token (User ID: 1, Token: `test_token_abc`)
2. Send a notification (User ID: 1, Title: "Welcome", Message: "Hello!")
3. View notifications (User ID: 1) → Should see the "Welcome" notification
4. Mark it as read → Should see "Read: Yes"

### Scenario 2: Multiple Users
1. Register device for User ID 1
2. Register device for User ID 2
3. Send notification to User ID 1
4. Send notification to User ID 2
5. View notifications for each user separately

### Scenario 3: Different Notification Types
1. Register a device
2. Send multiple notifications with different types:
   - General
   - Request Update
   - Report Ready
   - Subscription
   - Admin
3. View all notifications to see the different types

---

## Troubleshooting

### Error: "User with ID X does not exist"
**Solution**: Make sure the user exists in your database. You can:
- Create a user through Django admin: http://127.0.0.1:8000/admin/
- Or use an existing user ID from your `authentication_user` table

### Error: "Cannot resolve keyword 'device_token'"
**Solution**: This has been fixed. The correct field is `registration_token`.

### No push notification sent
**Reason**: Push notifications require:
1. Valid Firebase credentials in your `.env` file
2. A real FCM device token (not just `test_token_123`)
3. Firebase Cloud Messaging configured properly

For basic testing, you don't need actual push notifications - the in-app notifications will still work.

---

## Quick Reference

| Action | Location | What It Does |
|--------|----------|--------------|
| Register Device | Box 1 | Adds a device token to receive push notifications |
| Send Notification | Box 2 | Creates a notification and attempts to send push |
| View Notifications | Box 3 | Shows all notifications for a user |
| Mark as Read | Box 3 (in list) | Changes notification status to "read" |
| See All Devices | Box 4 | Lists all registered FCM devices |

---

## Testing Without Real Devices

If you don't have a real mobile device or FCM token, you can still test:

1. Use any fake token like: `fake_token_for_testing`
2. The notification will be created in the database
3. You can view it in Box 3
4. The push notification will fail (expected), but the notification itself works

To see push notifications work properly, you need:
- A real mobile app with Firebase SDK
- Or a web app with Firebase Web SDK
- Proper Firebase configuration in your `.env` file
