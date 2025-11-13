
### Phase 1: Admin Creates Plan (Backend)

**Endpoint:** `POST /api/admin/plans/`

**Request:**
```json
{
  "name": "Standard",
  "plan_type": "basic",
  "price_per_report": 29.99,
  "description": "Essential background check features for individuals",
  "identity_verification": true,
  "ssn_trace": true,
  "national_criminal_search": true,
  "sex_offender_registry": true,
  "employment_verification": false,
  "education_verification": false,
  "unlimited_county_search": false,
  "priority_support": false,
  "api_access": false
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Standard",
  "price_per_report": "29.99",
  "description": "Essential background check features",
  "is_active": true,
  "features": {
    "identity_verification": true,
    "ssn_trace": true,
    ...
  }
}
```

---

### Phase 2: Mobile App Fetches Plans

**Endpoint:** `GET /api/subscriptions/plans/`

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/api/subscriptions/plans/
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Basic Plan",
    "plan_type": "basic",
    "price_per_report": "25.00",
    "description": "Essential background check features for individuals",
    "is_active": true,
    "features": {
      "identity_verification": true,
      "ssn_trace": true,
      "national_criminal_search": true,
      "sex_offender_registry": true
    }
  },
  {
    "id": 2,
    "name": "Premium Report",
    "plan_type": "premium",
    "price_per_report": "50.00",
    "description": "Advanced features with unlimited searches",
    "is_active": true,
    "features": {
      "identity_verification": true,
      "ssn_trace": true,
      "national_criminal_search": true,
      "sex_offender_registry": true,
      "employment_verification": true,
      "education_verification": true,
      "unlimited_county_search": true
    }
  }
]
```

---

### Phase 3: User Selects Plan & Creates Checkout

**Endpoint:** `POST /api/subscriptions/create-checkout-session/`

**Headers:**
```
Authorization: Bearer <USER_JWT_TOKEN>
Content-Type: application/json
```

**Request:**
```json
{
  "plan_id": 1
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_a1b2c3d4...",
  "session_id": "cs_test_a1b2c3d4e5f6g7h8i9j0",
  "plan": {
    "id": 1,
    "name": "Basic Plan",
    "price_per_report": "25.00"
  }
}
```

**Mobile App Action:**
- Open `checkout_url` in WebView or browser
- User completes payment on Stripe hosted page
- Stripe redirects back to your app

---

### Phase 4: Stripe Processes Payment

**What Happens:**
1. User enters card details on Stripe page
2. Stripe processes payment (one-time payment, NOT recurring subscription)
3. Stripe sends webhook to: `POST /api/subscriptions/webhook/`
4. Your backend receives webhook events

**Important:** Your system uses ONE-TIME PAYMENTS, not recurring subscriptions. Each report purchase is a separate payment.

**Webhook Events Received:**

#### Event 1: `checkout.session.completed`
```json
{
  "type": "checkout.session.completed",
  "data": {
    "object": {
      "id": "cs_test_a1b2c3d4...",
      "customer": "cus_abc123",
      "payment_status": "paid",
      "amount_total": 2500,
      "mode": "payment",
      "metadata": {
        "user_id": "42",
        "plan_id": "1"
      }
    }
  }
}
```


#### Event 2: `payment_intent.succeeded`
```json
{
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_abc123",
      "amount": 2500,
      "currency": "usd",
      "status": "succeeded"
    }
  }
}
```

#### Event 3: `invoice.payment_succeeded`
```json
{
  "type": "invoice.payment_succeeded",
  "data": {
    "object": {
      "id": "in_xyz789",
      "subscription": "sub_xyz789",
      "amount_paid": 2500,
      "status": "paid"
    }
  }
}
```

---

### Phase 5: User Gets Subscription Confirmation

**Mobile App Calls:** `GET /api/subscriptions/verify-checkout-session/?session_id=cs_test_a1b2c3d4e5f6g7h8i9j0`

**Headers:**
```
Authorization: Bearer <USER_JWT_TOKEN>
```

**Response:**
```json
{
  "success": true,
  "subscription": {
    "plan": "Basic Plan",
    "status": "active",
    "total_reports_purchased": 10,
    "reports_used": 0,
    "available_reports": 10,
    "start_date": "2024-11-12T10:30:00Z"
  },
  "payment": {
    "amount": 25.00,
    "currency": "USD",
    "status": "succeeded"
  }
}
```

---

### Phase 6: User Checks Subscription

**Endpoint:** `GET /api/subscriptions/`

**Headers:**
```
Authorization: Bearer <USER_JWT_TOKEN>
```

**Response:**
```json
{
  "id": 1,
  "plan": {
    "id": 1,
    "name": "Basic Plan",
    "price_per_report": "25.00",
    "features": {...}
  },
  "status": "active",
  "total_reports_purchased": 10,
  "reports_used": 0,
  "available_reports": 10,
  "start_date": "2024-11-12T10:30:00Z",
  "next_billing_date": "2024-12-12T10:30:00Z"
}
```

---

### Phase 7: View Payment History

**Endpoint:** `GET /api/subscriptions/payment-history/`

**Headers:**
```
Authorization: Bearer <USER_JWT_TOKEN>
```

**Response:**
```json
[
  {
    "id": 1,
    "amount": "25.00",
    "currency": "USD",
    "status": "succeeded",
    "reports_purchased": 10,
    "description": "Subscription to Basic Plan",
    "stripe_payment_intent_id": "pi_abc123",
    "created_at": "2024-11-12T10:30:00Z"
  },
  {
    "id": 2,
    "amount": "25.00",
    "currency": "USD",
    "status": "succeeded",
    "reports_purchased": 5,
    "description": "Additional reports purchase",
    "stripe_payment_intent_id": "pi_def456",
    "created_at": "2024-11-11T15:20:00Z"
  }
]
```

---

## Admin Endpoints - View All Transactions

### 1. View All Payment Transactions

**Endpoint:** `GET /api/admin/payments/`

**Query Parameters:**
- `user_id` (optional) - Filter by user
- `status` (optional) - Filter by status (succeeded, failed, pending)
- `start_date` (optional) - Filter from date (YYYY-MM-DD)
- `end_date` (optional) - Filter to date (YYYY-MM-DD)

**Response:**
```json
{
  "count": 50,
  "total_amount": 1500.00,
  "payments": [
    {
      "id": 1,
      "user": {
        "id": 42,
        "username": "john_doe",
        "email": "john@example.com"
      },
      "plan": {
        "name": "Basic Plan",
        "price_per_report": "25.00"
      },
      "amount": "25.00",
      "currency": "USD",
      "status": "succeeded",
      "stripe_payment_intent_id": "pi_abc123",
      "description": "Purchase: Basic Plan",
      "created_at": "2024-11-12T10:30:00Z"
    }
  ]
}
```

---

##  Setup Stripe Webhook (If Not Done)

### Step 1: Get Webhook URL
```
https://h2o427-backend.onrender.com/api/subscriptions/webhook/
```



# Payment Analytics from ADMIN

### Test Payment History Endpoint

```bash
# Get all payments
curl -X GET http://127.0.0.1:8000/api/admin/payments/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Filter successful payments only
curl -X GET "http://127.0.0.1:8000/api/admin/payments/?status=succeeded" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Get November 2024 payments
curl -X GET "http://127.0.0.1:8000/api/admin/payments/?start_date=2024-11-01&end_date=2024-11-30" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Test Analytics Endpoint

```bash
curl -X GET http://127.0.0.1:8000/api/admin/analytics/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```




**Example Requests:**

```bash
# Get all successful payments
curl -X GET "http://127.0.0.1:8000/api/admin/payments/?status=succeeded" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Get payments for specific user
curl -X GET "http://127.0.0.1:8000/api/admin/payments/?user_id=42" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Get payments in date range
curl -X GET "http://127.0.0.1:8000/api/admin/payments/?start_date=2024-11-01&end_date=2024-11-30" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# Combine filters
curl -X GET "http://127.0.0.1:8000/api/admin/payments/?status=succeeded&start_date=2024-11-13" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**

```json
{
  "count": 50,
  "total_amount": "1250.00",
  "filters_applied": {
    "user_id": null,
    "status": "succeeded",
    "start_date": "2024-11-01",
    "end_date": null
  },
  "payments": [
    {
      "id": 1,
      "user": {
        "id": 42,
        "username": "john_doe",
        "email": "john@example.com",
        "full_name": "John Doe"
      },
      "plan": "Basic Plan",
      "amount": "25.00",
      "currency": "USD",
      "status": "succeeded",
      "reports_purchased": 10,
      "description": "Subscription to Basic Plan",
      "stripe_payment_intent_id": "pi_abc123def456",
      "stripe_charge_id": "ch_xyz789ghi012",
      "failure_reason": null,
      "created_at": "2024-11-12T10:30:00Z",
      "updated_at": "2024-11-12T10:30:00Z"
    },
    {
      "id": 2,
      "user": {
        "id": 43,
        "username": "jane_smith",
        "email": "jane@example.com",
        "full_name": "Jane Smith"
      },
      "plan": "Premium Report",
      "amount": "50.00",
      "currency": "USD",
      "status": "succeeded",
      "reports_purchased": 5,
      "description": "Additional reports purchase",
      "stripe_payment_intent_id": "pi_def456ghi789",
      "stripe_charge_id": "ch_ghi012jkl345",
      "failure_reason": null,
      "created_at": "2024-11-11T15:20:00Z",
      "updated_at": "2024-11-11T15:20:00Z"
    }
  ]
}
```

**Use Cases:**
- Track all payment transactions
- Identify failed payments for follow-up
- Generate financial reports
- Audit user payment history
- Calculate revenue by date range

---

## Analytics Dashboard

### 2. Get Subscription Analytics
**GET** `/api/admin/analytics/`

Get comprehensive analytics including revenue, subscriptions, popular plans, and trends.

**No parameters required** - Returns complete analytics overview

**Example Request:**

```bash
curl -X GET http://127.0.0.1:8000/api/admin/analytics/ \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**

```json
{
  "overview": {
    "total_revenue": "15000.00",
    "active_subscriptions": 150,
    "total_transactions": 500,
    "successful_transactions": 475,
    "failed_transactions": 25,
    "success_rate": "95.0%"
  },
  "popular_plans": [
    {
      "id": 1,
      "name": "Basic Plan",
      "price_per_report": "25.00",
      "subscribers": 85,
      "revenue": "8500.00"
    },
      
  ],
  "revenue_by_month": [
    {
      "month": "2024-01",
      "revenue": "800.00",
      "transactions": 32
    },
    {
      "id": 44,
      "user": "corporate_user",
      "amount": "250.00",
      "plan": "Premium Report",
      "reports_purchased": 50,
      "created_at": "2024-11-11T14:15:00Z"
    },
    {
      "id": 43,
      "user": "jane_smith",
      "amount": "75.00",
      "plan": "Basic Plan",
      "reports_purchased": 15,
      "created_at": "2024-11-10T09:45:00Z"
    }
  ]
}
```
