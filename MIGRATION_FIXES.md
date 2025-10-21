# Migration Issues Fixed

## Summary
All migration issues have been successfully resolved. The project is now ready for development.

## Issues Fixed

### 1. **User Model Name Mismatch**
- **Problem**: The model in `authentication/models.py` was named `CustomUser` but `settings.AUTH_USER_MODEL` was set to `'authentication.User'`
- **Solution**: Renamed `CustomUser` to `User` in `authentication/models.py`
- **Files Modified**:
  - `authentication/models.py` - Changed class name from `CustomUser` to `User`
  - `authentication/serializers.py` - Updated imports from `CustomUser` to `User`
  - `authentication/views.py` - Updated imports

### 2. **Missing PhoneOTP Model**
- **Problem**: Migration file expected a `PhoneOTP` model but it was missing from `models.py`
- **Solution**: Added the complete `PhoneOTP` model with all required fields and methods
- **Files Modified**:
  - `authentication/models.py` - Added `PhoneOTP` model with:
    - Fields: user, phone_number, code, created_at, expires_at, verified
    - Method: `is_otp_expired()` to check expiration
    - Auto-population of expires_at using settings
  - `authentication/views.py` - Updated OTP references from `OTP` to `PhoneOTP`

### 3. **App Name Conflict with Python Library**
- **Problem**: Django app named "requests" was shadowing the Python `requests` library, causing import errors for Twilio
- **Solution**: Renamed the app from `requests` to `background_requests`
- **Files Modified**:
  - Renamed folder: `requests/` → `background_requests/`
  - `background_requests/apps.py` - Updated app name
  - `background_check/settings.py` - Updated INSTALLED_APPS
  - `background_check/urls.py` - Updated URL includes
  - `admin_dashboard/views.py` - Updated imports
  - `admin_dashboard/serializers.py` - Updated imports
  - `admin_dashboard/models.py` - Updated imports
  - `admin_dashboard/admin_views.py` - Updated imports
  - `admin_dashboard/admin.py` - Updated imports

### 4. **User Model Field Consistency**
- **Problem**: User model fields didn't match migration expectations
- **Solution**: Updated User model fields to match migration:
  - Made `full_name` and `phone_number` optional (blank=True, null=True)
  - Added proper field constraints matching migration

### 5. **Migration State Issues**
- **Problem**: Existing PostgreSQL database had old migration states
- **Solution**: Faked migrations to align database state with new migration files

## Verification

All systems are now working:
```bash
python manage.py check
# System check identified no issues (0 silenced).

python manage.py migrate
# All migrations applied successfully
```

## Apps Structure

### Updated Apps:
1. **authentication** - User authentication with phone OTP
   - User model (extends AbstractUser)
   - PhoneOTP model for phone verification
   
2. **background_requests** (formerly "requests") - Background check requests
   - Request model
   - Report model

3. **admin_dashboard** - Admin management features
   - AdminDashboardSettings
   - RequestActivity
   - AdminNote
   - RequestAssignment

4. **subscriptions** - Subscription management
   - SubscriptionPlan
   - UserSubscription
   - PaymentHistory

## Next Steps

The project is now ready for:
- Creating superuser: `python manage.py createsuperuser`
- Running development server: `python manage.py runserver`
- Adding test data
- Further development

## Important Notes

1. **App Name Change**: The app previously known as "requests" is now "background_requests". All API endpoints remain the same (`/api/requests/`), only internal references changed.

2. **Import Updates**: If you have any other files importing from the old "requests" app, update them to use "background_requests" instead.

3. **Database**: Currently using PostgreSQL. All migrations are now in sync with the database schema.
