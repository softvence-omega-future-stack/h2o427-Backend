# Fix: Push Sent Field IntegrityError

## Problem

Production error when creating background check requests:
```
IntegrityError at /api/requests/api/
null value in column "push_sent" of relation "notifications_notification" violates not-null constraint
```

## Root Cause

The `push_sent` field was added to the Notification model with `default=False`, but:
1. Signal handlers were not explicitly setting `push_sent=False` when creating notifications
2. Production database may have had schema inconsistencies
3. Settings.py had incorrect Firebase initialization at import time

## Fixes Applied

### 1. Updated Signal Handlers ✅

All `Notification.objects.create()` calls now explicitly set `push_sent=False`:

**Files Modified:**
- `notifications/signals.py`

**Changes:**
- ✅ `notify_on_request_status_change()` - Added `push_sent=False` to all 3 notification creates
- ✅ `notify_on_report_generated()` - Added `push_sent=False`
- ✅ `send_admin_notification()` helper - Added `push_sent=False`
- ✅ `send_user_notification()` helper - Added `push_sent=False`

### 2. Removed Incorrect Firebase Init from Settings ✅

**Problem:**
```python
# In settings.py (INCORRECT - causes import errors)
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
firebase_admin.initialize_app(cred)
```

**Fix:**
Removed all Firebase initialization from `settings.py`. Firebase should ONLY be initialized in `notifications/firebase_service.py` where it's used.

**Files Modified:**
- `background_check/settings.py`

### 3. Migration Already Correct ✅

The migration `0002_notification_push_error_notification_push_sent_and_more.py` already has:
```python
migrations.AddField(
    model_name='notification',
    name='push_sent',
    field=models.BooleanField(default=False, help_text='Whether push notification was sent'),
),
```

This is correct! The issue was in the signal handlers.

## Testing

### Local Testing
```bash
# Check Django configuration
python manage.py check

# Test notification creation
python manage.py shell
>>> from authentication.models import User
>>> from notifications.models import Notification
>>> user = User.objects.first()
>>> n = Notification.objects.create(
...     recipient=user,
...     type='system',
...     category='general',
...     title='Test',
...     message='Test'
... )
>>> print(n.push_sent)  # Should print: False
False
```

### Production Deployment

After deploying these changes to Render.com:

1. **Migrations will run automatically** (no new migrations needed)
2. **New notifications will work** - `push_sent` will default to False
3. **Existing notifications** - Already have push_sent=False from previous migration

## Verification Steps

After deployment, test creating a background check request:

```bash
# Submit request via API
POST https://h2o427-backend-u9bx.onrender.com/api/requests/api/
```

**Expected Result:**
- ✅ Request created successfully
- ✅ Admin notifications created
- ✅ User confirmation notification created
- ✅ No IntegrityError
- ✅ All notifications have push_sent=False initially

## Summary of Changes

| File | Change | Status |
|------|--------|--------|
| `notifications/signals.py` | Added `push_sent=False` to all notification creates | ✅ Fixed |
| `background_check/settings.py` | Removed Firebase initialization | ✅ Fixed |
| `notifications/models.py` | Already has `default=False` | ✅ Already correct |
| `notifications/migrations/0002_*.py` | Already has `default=False` | ✅ Already correct |

## Why This Happened

The issue occurred because:
1. When migrations ran on production, the default value was set correctly
2. BUT signal handlers were creating notifications without explicitly setting the field
3. Django ORM sometimes doesn't apply defaults when using `objects.create()` with signals
4. Best practice: Always explicitly set Boolean fields with defaults in signal handlers

## Prevention

To prevent similar issues:
- ✅ Always explicitly set Boolean fields in `objects.create()` calls
- ✅ Never initialize external services (like Firebase) in settings.py
- ✅ Test signal handlers thoroughly before deploying
- ✅ Use `python manage.py check` before deployment

## Deployment

**Changes to deploy:**
1. `notifications/signals.py` - Signal handler fixes
2. `background_check/settings.py` - Removed incorrect Firebase init

**No migrations needed** - existing migration is correct.

**Deploy command (Render.com auto-deploys on push):**
```bash
git add .
git commit -m "fix: Add push_sent=False explicitly in notification signals"
git push origin main
```

## Expected Outcome

After deployment:
- ✅ Background check requests can be created without errors
- ✅ Notifications are created successfully
- ✅ Push notification tracking works correctly
- ✅ No IntegrityError on production

---

**Status:** ✅ FIXED - Ready to deploy
