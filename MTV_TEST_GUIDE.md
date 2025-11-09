# MTV Simple UI Test Guide

## Starting the Server

```bash
python manage.py runserver
```

## Test Flow URLs

### 1. Registration Page
- **URL**: http://localhost:8000/api/auth/register-page/
- **Test**: Fill form with username, email, full_name, password, confirm_password
- **Expected**: Redirects to login page on success

### 2. Login Page
- **URL**: http://localhost:8000/api/auth/login-page/
- **Test**: Login with email and password
- **Expected**: Redirects to dashboard

### 3. Dashboard
- **URL**: http://localhost:8000/api/subscriptions/my-dashboard/
- **Test**: View subscription info and requests
- **Expected**: Shows subscription details and list of requests

### 4. Select Plan Page
- **URL**: http://localhost:8000/api/subscriptions/plans-page/
- **Test**: View available plans and select one
- **Expected**: Shows all active plans with features

### 5. Purchase Reports Page
- **URL**: http://localhost:8000/api/subscriptions/purchase-page/
- **Test**: Purchase additional reports using Stripe
- **Required**: Stripe configuration in .env file
- **Test Card**: 4242 4242 4242 4242 (any future date, any CVC)
- **Expected**: Processes payment and adds reports to account

### 6. Submit Request Page
- **URL**: http://localhost:8000/api/requests/submit-page/
- **Test**: Submit background check request
- **Expected**: Creates request and redirects to success page

### 7. Request Success Page
- **URL**: http://localhost:8000/api/requests/request-success/<request_id>/
- **Test**: View confirmation after submitting request
- **Expected**: Shows request details and status

### 8. View Report Page
- **URL**: http://localhost:8000/api/requests/view-report/<request_id>/
- **Test**: View completed background check report
- **Expected**: Shows full report with all sections

## Complete Test Workflow

1. Start server: `python manage.py runserver`
2. Go to http://localhost:8000/api/auth/register-page/
3. Register new user account
4. Login at http://localhost:8000/api/auth/login-page/
5. View dashboard (auto-redirect after login)
6. Click "Select Plan" and choose a plan
7. Go to "Purchase Reports" and buy reports
8. Submit a background check request
9. View the request on dashboard
10. View report when ready

## Notes

- All pages have NO styling (as requested)
- Forms use Django CSRF protection
- Login required for most pages
- Messages display success/error notifications
- Stripe integration requires STRIPE_PUBLISHABLE_KEY in settings

## Troubleshooting

If you get "Please select a plan first":
- Go to plans-page and select a plan

If you get "No reports available":
- Go to purchase-page and buy reports

If Stripe payment fails:
- Check STRIPE_PUBLISHABLE_KEY and STRIPE_SECRET_KEY in .env
- Use test card: 4242 4242 4242 4242
