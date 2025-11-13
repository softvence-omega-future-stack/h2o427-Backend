
## Quick Reference - All Endpoints

**Authentication:**
- POST `/api/auth/register/` - Register new user
- POST `/api/auth/login/` - Login and get JWT token

**Subscriptions:**
- GET `/api/subscriptions/plans/` - Get all available plans
- POST `/api/subscriptions/subscription/` - Create/select subscription plan
- GET `/api/subscriptions/subscription/` - Get current subscription
- GET `/api/subscriptions/usage/` - Get subscription usage details
- GET `/api/subscriptions/payment-history/` - Get payment history

**Payments:**
- POST `/api/subscriptions/purchase-report/` - Create Stripe Checkout Session (returns checkout URL)
- GET `/api/subscriptions/confirm-payment/?session_id=xxx` - Confirm payment (automatic callback)

**Background Checks:**
- POST `/api/requests/api/` - Submit background check request
- GET `/api/requests/api/` - Get all my requests
- GET `/api/requests/api/{id}/` - Get specific request details
- GET `/api/requests/reports/{id}/` - Get request report

---

## 1. AUTHENTICATION ENDPOINTS

### Register User
**POST** `/api/auth/register/`

**Body (JSON):**
```json
{
    "username": "testuser123",
    "email": "test@example.com",
    "password": "TestPass123!",
    "confirm_password": "TestPass123!",
    "full_name": "Test User"
}
```

**Response:**
```json
{
    "message": "User registered successfully",
    "user": {
        "id": 1,
        "username": "testuser123",
        "email": "test@example.com",
        "full_name": "Test User"
    }
}
```

---

### Login
**POST** `/api/auth/login/`

**Body (JSON):**
```json
{
    "email": "test@example.com",
    "password": "TestPass123!"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "username": "testuser123",
        "email": "test@example.com"
    }
}
```

**Important:** Save the `access` token for subsequent requests!

---

## 2. SUBSCRIPTION PLAN ENDPOINTS

### Get All Plans
**GET** `/api/subscriptions/plans/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "Basic Plan",
        "price_per_report": "25.00",
        "description": "Basic background check",
        "is_active": true,
        "identity_verification": true,
        "ssn_trace": false,
        "national_criminal_search": true
    }
]
```

---

### Create/Get User Subscription
**POST** `/api/subscriptions/subscription/`

**Purpose:** Select a plan for your account. This does NOT charge you - it only assigns a plan. You must purchase reports separately.

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "plan_id": 1
}
```

**Response:**
```json
{
    "message": "Subscription created successfully",
    "subscription": {
        "id": 1,
        "user": 1,
        "plan": {
            "id": 1,
            "name": "Basic Plan",
            "price_per_report": "25.00"
        },
        "free_trial_used": false,
        "total_reports_purchased": 0,
        "total_reports_used": 0,
        "available_reports": 0,
        "can_make_request": false
    }
}
```

**Important Notes:**
- This endpoint only selects a plan - no payment is made
- To get reports, use the purchase-report endpoint
- First request can use free trial if available
- URL must have trailing slash: `/api/subscriptions/subscription/`

---

### Get Current Subscription
**GET** `/api/subscriptions/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
    "id": 1,
    "plan": {
        "id": 1,
        "name": "Basic Plan",
        "price_per_report": "25.00"
    },
    "free_trial_used": false,
    "total_reports_purchased": 5,
    "total_reports_used": 0,
    "available_reports": 5,
    "can_make_request": true
}
```

---

## 3. PAYMENT ENDPOINTS (STRIPE CHECKOUT)

### Purchase Reports - Create Checkout Session
**POST** `/api/subscriptions/purchase-report/`

**Description:** Creates a Stripe Checkout Session and returns a URL to redirect the user to Stripe's official payment page.

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "plan_id": 1,
    "quantity": 5
}
```

**Response:**
```json
{
    "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_xxxxxxxxxxxxx",
    "session_id": "cs_test_xxxxxxxxxxxxx",
    "amount": 125.0,
    "quantity": 5,
    "plan": "Basic Plan",
    "plan_price": 25.0
}
```

**Next Steps:**
1. **In Browser/Frontend:** Redirect user to the `checkout_url`
2. **User completes payment** on Stripe's secure checkout page
3. **Stripe redirects** back to: `/api/subscriptions/confirm-payment/?session_id=cs_test_xxx`
4. **Backend confirms** payment and adds reports automatically

**Important:** 
- The `checkout_url` is where you redirect the user in the browser/frontend
- After payment, Stripe automatically redirects to the confirm-payment endpoint
- Reports are added automatically when payment succeeds

---

### Confirm Payment (Automatic Callback)
**GET** `/api/subscriptions/confirm-payment/?session_id={SESSION_ID}`

**Description:** This endpoint is automatically called by Stripe after successful payment. You don't need to call it manually in Postman.

**How It Works:**
1. User completes payment on Stripe checkout page
2. Stripe redirects to: `https://yourdomain.com/api/subscriptions/confirm-payment/?session_id=cs_test_xxx`
3. Backend verifies payment and adds reports
4. Returns success response

**Response:**
```json
{
    "message": "Payment confirmed successfully",
    "reports_added": 5,
    "available_reports": 5,
    "subscription": {
        "id": 1,
        "plan": {
            "id": 1,
            "name": "Basic Plan",
            "price_per_report": "25.00"
        },
        "total_reports_purchased": 5,
        "total_reports_used": 0,
        "available_reports": 5
    }
}
```

**Note:** In production, this URL should be your actual domain. For testing, you can manually call this endpoint with a test session_id after payment.

---


**Requirements:**
- Must have selected a plan first (POST `/api/subscriptions/subscription/`)
- Must be authenticated

**Alternative Flow:**
Instead of:
1. POST `/api/subscriptions/purchase-report/` (create payment intent)
2. Use Stripe.js to process payment with card
3. POST `/api/subscriptions/confirm-payment/` (confirm payment)

Use this:
1. POST `/api/subscriptions/test-purchase/` (directly add reports)

---

### Get Payment History
**GET** `/api/subscriptions/payment-history/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
[
    {
        "id": 1,
        "amount": "125.00",
        "quantity": 5,
        "payment_method": "stripe",
        "stripe_payment_intent_id": "pi_3xxxxxxxxxxxxx",
        "status": "completed",
        "created_at": "2025-11-09T10:30:00Z"
    }
]
```

---

## 4. BACKGROUND CHECK REQUEST ENDPOINTS

### Submit Background Check Request
**POST** `/api/requests/api/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Body (JSON):**
```json
{
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone_number": "+1234567890",
    "dob": "1990-05-15",
    "city": "New York",
    "state": "NY"
}
```

**Response:**
```json
{
    "id": 1,
    "user": 1,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone_number": "+1234567890",
    "dob": "1990-05-15",
    "city": "New York",
    "state": "NY",
    "status": "Pending",
    "created_at": "2025-11-09T10:35:00Z",
    "updated_at": "2025-11-09T10:35:00Z"
}
```

---

### Get All My Requests
**GET** `/api/requests/api/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
[
    {
        "id": 1,
        "name": "John Doe",
        "email": "john.doe@example.com",
        "status": "Pending",
        "created_at": "2025-11-09T10:35:00Z"
    }
]
```

---

### Get Specific Request
**GET** `/api/requests/api/{request_id}/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Example:** `/api/requests/api/1/`

**Response:**
```json
{
    "id": 1,
    "user": 1,
    "name": "John Doe",
    "email": "john.doe@example.com",
    "phone_number": "+1234567890",
    "dob": "1990-05-15",
    "city": "New York",
    "state": "NY",
    "status": "Completed",
    "created_at": "2025-11-09T10:35:00Z",
    "updated_at": "2025-11-09T11:00:00Z"
}
```

---

### Get Request Report
**GET** `/api/requests/reports/{request_id}/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Example:** `/api/requests/reports/1/`

**Response:**
```json
{
    "id": 1,
    "request": 1,
    "verification_status": "Verified",
    "ssn_validation": "Valid",
    "federal_criminal_records": "No records found",
    "state_criminal_records": "No records found",
    "education_verified": true,
    "final_summary": "Background check completed successfully",
    "generated_at": "2025-11-09T11:00:00Z"
}
```

---

## 5. COMPLETE TEST WORKFLOW IN POSTMAN

### Collection Setup

1. **Create Environment Variables:**
   - `base_url`: `http://localhost:8000`
   - `access_token`: (will be set after login)
   - `plan_id`: (will be set after getting plans)
   - `payment_intent_id`: (will be set after purchase)
   - `request_id`: (will be set after creating request)

---

### Test Steps:

#### Step 1: Register
```
POST {{base_url}}/api/auth/register/
Body: {username, email, password, confirm_password, full_name}
```

#### Step 2: Login
```
POST {{base_url}}/api/auth/login/
Body: {email, password}
Save: access token to {{access_token}}
```

#### Step 3: Get Plans
```
GET {{base_url}}/api/subscriptions/plans/
Header: Authorization: Bearer {{access_token}}
Save: First plan ID to {{plan_id}}
```

#### Step 4: Create Subscription
```
POST {{base_url}}/api/subscriptions/subscription/
Header: Authorization: Bearer {{access_token}}
Body: {"plan_id": {{plan_id}}}
```

#### Step 5: Purchase Reports - OPTION A (With Stripe Checkout)
```
POST {{base_url}}/api/subscriptions/purchase-report/
Header: Authorization: Bearer {{access_token}}
Body: {"plan_id": {{plan_id}}, "quantity": 5}

Response will contain:
{
  "checkout_url": "https://checkout.stripe.com/c/pay/...",
  "session_id": "cs_test_..."
}

Then:
1. Open the checkout_url in a browser
2. Complete payment on Stripe's page
3. Stripe redirects to confirm-payment endpoint automatically
4. Reports are added to your account
```

#### Step 5: Purchase Reports - OPTION B (Test Mode - No Stripe)
** USE THIS FOR POSTMAN TESTING**
```
POST {{base_url}}/api/subscriptions/test-purchase/
Header: Authorization: Bearer {{access_token}}
Body: {"quantity": 5}

This directly adds reports without Stripe payment.
```

#### Step 6: Check Subscription (Verify Reports Added)
```
GET {{base_url}}/api/subscriptions/
Header: Authorization: Bearer {{access_token}}
Verify: available_reports should be 5
```

#### Step 7: Submit Background Check Request
```
POST {{base_url}}/api/requests/api/
Header: Authorization: Bearer {{access_token}}
Body: {name, email, phone_number, dob, city, state}
Save: Request ID to {{request_id}}
```

#### Step 8: Check Updated Subscription (Verify Report Used)
```
GET {{base_url}}/api/subscriptions/
Header: Authorization: Bearer {{access_token}}
Verify: available_reports should be 4, total_reports_used should be 1
```

#### Step 9: Get Request Details
```
GET {{base_url}}/api/requests/api/{{request_id}}/
Header: Authorization: Bearer {{access_token}}
```

#### Step 11: Get All Requests
```
GET {{base_url}}/api/requests/api/
Header: Authorization: Bearer {{access_token}}
```
