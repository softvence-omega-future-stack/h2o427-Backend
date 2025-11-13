# Complete System Flow - Admin & User Endpoints

## System Overview

**Flow:** Admin creates plans → User submits form → User purchases plan → Admin gets notified → Admin processes request → Admin uploads report → User gets notified → User views/downloads report

---

## PART 1: ADMIN SIDE - PLAN MANAGEMENT

### Admin Authentication
First, admin needs to login:

**Endpoint:** `POST /api/auth/login/`
```json
{
  "username": "admin",
  "password": "admin_password"
}
```
**Response:** Get `access` token for all admin requests

---

### 1. Create Plan
**Endpoint:** `POST /api/admin/plans/`

**Headers:**
```
Authorization: Bearer ADMIN_TOKEN
Content-Type: application/json
```

**Request:**
```json
{
  "name": "Basic Plan",
  "plan_type": "basic",
  "price_per_report": 25.00,
  "description": "Essential background check features",
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
  "name": "Basic Plan",
  "price_per_report": "25.00",
  "is_active": true,
  "created_at": "2024-11-13T10:00:00Z"
}
```

---

### 2. View All Plans
**Endpoint:** `GET /api/admin/plans/`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Basic Plan",
    "price_per_report": "25.00",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Premium Plan",
    "price_per_report": "50.00",
    "is_active": true
  }
]
```

---

### 3. Edit Plan
**Endpoint:** `PATCH /api/admin/plans/<plan_id>/`

**Example:** `PATCH /api/admin/plans/1/`

**Request:**
```json
{
  "name": "Basic Plan Updated",
  "price_per_report": 30.00,
  "description": "Updated description"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Basic Plan Updated",
  "price_per_report": "30.00",
  "updated_at": "2024-11-13T11:00:00Z"
}
```

---

### 4. Delete Plan
**Endpoint:** `DELETE /api/admin/plans/<plan_id>/`

**Example:** `DELETE /api/admin/plans/1/?mode=soft`

**Query Parameters:**
- `mode=soft` - Deactivate plan (default)
- `mode=hard` - Permanently delete plan

**Response (Soft Delete):**
```json
{
  "message": "Plan deactivated successfully",
  "plan_id": 1,
  "is_active": false
}
```

**Response (Hard Delete):**
```json
{
  "message": "Plan deleted permanently",
  "plan_id": 1
}
```

---

## PART 2: USER SIDE - VIEW PLANS & SUBMIT REQUEST

### User Authentication
**Endpoint:** `POST /api/auth/login/`
```json
{
  "username": "user123",
  "password": "user_password"
}
```
**Response:** Get `access` token

---

### 5. User Views Available Plans
**Endpoint:** `GET /api/subscriptions/plans/`

**Headers:** None required (public endpoint)

**Response:**
```json
[
  {
    "id": 1,
    "name": "Basic Plan",
    "plan_type": "basic",
    "price_per_report": "25.00",
    "description": "Essential background check features",
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
    "name": "Premium Plan",
    "plan_type": "premium",
    "price_per_report": "50.00",
    "description": "Complete background investigation",
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

**Connection:** This shows plans created by admin in Step 1-4

---

### 6. User Submits Background Check Form
**Endpoint:** `POST /api/requests/api/`

**Headers:**
```
Authorization: Bearer USER_TOKEN
Content-Type: application/json
```

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "ssn": "123-45-6789",
  "email": "john.doe@example.com",
  "phone": "+1234567890",
  "address": "123 Main St",
  "city": "New York",
  "state": "NY",
  "zip_code": "10001",
  "country": "USA"
}
```

**Response:**
```json
{
  "id": 42,
  "first_name": "John",
  "last_name": "Doe",
  "status": "pending",
  "created_at": "2024-11-13T12:00:00Z",
  "message": "Request submitted successfully"
}
```

**Status:** `pending` (waiting for payment)

---

## PART 3: USER PAYMENT FLOW

### 7. User Selects Plan & Creates Payment
**Endpoint:** `POST /api/requests/api/<request_id>/select-pricing/`

**Example:** `POST /api/requests/api/42/select-pricing/`

**Headers:**
```
Authorization: Bearer USER_TOKEN
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
  "success": true,
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_a1b2c3d4...",
  "session_id": "cs_test_a1b2c3d4e5f6g7h8",
  "plan": {
    "id": 1,
    "name": "Basic Plan",
    "type": "basic"
  },
  "amount": "25.00",
  "message": "Redirect user to checkout_url to complete payment"
}
```

**Action:** User opens `checkout_url` and completes payment with Stripe

**Connection:** Uses plan_id from Step 5 (user views available plans)

---

### 8. Payment Confirmation (Automatic)
**Endpoint:** `GET /api/requests/api/<request_id>/confirm-payment/`

**This happens automatically after Stripe payment**

**Response:**
```json
{
  "status": "success",
  "message": "Payment confirmed successfully",
  "request": {
    "id": 42,
    "status": "paid",
    "amount_paid": "25.00"
  }
}
```

**Status:** Changes from `pending` → `paid`

---

### 9. Stripe Webhook (Background)
**Endpoint:** `POST /api/subscriptions/webhook/`

**Called by Stripe automatically**

**Actions:**
- Creates PaymentHistory record
- Updates UserSubscription
- Triggers notification to admin

---

## PART 4: ADMIN GETS NOTIFIED & PROCESSES REQUEST

### 10. Admin Views All Requests
**Endpoint:** `GET /api/admin/dashboard/requests/`

**Headers:**
```
Authorization: Bearer ADMIN_TOKEN
```

**Query Parameters:**
- `status=paid` - Filter by status
- `search=John` - Search by name
- `ordering=-created_at` - Sort by date

**Response:**
```json
{
  "count": 10,
  "results": [
    {
      "id": 42,
      "user": {
        "id": 5,
        "username": "user123",
        "email": "user@example.com"
      },
      "first_name": "John",
      "last_name": "Doe",
      "status": "paid",
      "payment_status": "paid",
      "created_at": "2024-11-13T12:00:00Z",
      "has_report": false
    }
  ]
}
```

**Connection:** Shows requests from Step 6 that are now `paid` from Step 8

---

### 11. Admin Views Request Details
**Endpoint:** `GET /api/admin/dashboard/requests/<request_id>/`

**Example:** `GET /api/admin/dashboard/requests/42/`

**Response:**
```json
{
  "id": 42,
  "user": {
    "id": 5,
    "username": "user123",
    "email": "user@example.com",
    "phone": "+1234567890"
  },
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-01-15",
  "ssn": "123-45-6789",
  "email": "john.doe@example.com",
  "address": "123 Main St, New York, NY 10001",
  "status": "paid",
  "payment_status": "paid",
  "amount_paid": "25.00",
  "plan": {
    "id": 1,
    "name": "Basic Plan"
  },
  "notes": [],
  "created_at": "2024-11-13T12:00:00Z",
  "updated_at": "2024-11-13T12:30:00Z"
}
```

---

### 12. Admin Updates Status to "In Progress"
**Endpoint:** `PATCH /api/admin/dashboard/requests/<request_id>/status/`

**Example:** `PATCH /api/admin/dashboard/requests/42/status/`

**Request:**
```json
{
  "status": "in_progress"
}
```

**Response:**
```json
{
  "id": 42,
  "status": "in_progress",
  "updated_at": "2024-11-13T13:00:00Z",
  "message": "Status updated successfully"
}
```

**Status:** Changes from `paid` → `in_progress`

**Action:** User receives notification: "Your background check is now being processed"

---

### 13. Admin Adds Notes (Optional)
**Endpoint:** `POST /api/admin/dashboard/requests/<request_id>/notes/`

**Request:**
```json
{
  "note": "Started verification process. Contacted previous employer."
}
```

**Response:**
```json
{
  "id": 1,
  "note": "Started verification process. Contacted previous employer.",
  "created_by": "admin",
  "created_at": "2024-11-13T13:30:00Z"
}
```

---

## PART 5: ADMIN COMPLETES REPORT

### 14. Admin Uploads Report PDF
**Endpoint:** `POST /api/admin/reports/upload/`

**Headers:**
```
Authorization: Bearer ADMIN_TOKEN
Content-Type: multipart/form-data
```

**Request (Form Data):**
```
request_id: 42
report_file: [PDF file]
report_type: basic
```

**Response:**
```json
{
  "id": 1,
  "request_id": 42,
  "report_type": "basic",
  "file_url": "/media/reports/report_42_20241113.pdf",
  "uploaded_at": "2024-11-13T14:00:00Z",
  "message": "Report uploaded successfully"
}
```

---

### 15. Admin Updates Status to "Completed"
**Endpoint:** `PATCH /api/admin/dashboard/requests/<request_id>/status/`

**Request:**
```json
{
  "status": "completed"
}
```

**Response:**
```json
{
  "id": 42,
  "status": "completed",
  "updated_at": "2024-11-13T14:00:00Z",
  "message": "Status updated successfully"
}
```

**Status:** Changes from `in_progress` → `completed`

**Action:** User receives notification: "Your background check is completed! View your report now."

---

## PART 6: USER VIEWS & DOWNLOADS REPORT

### 16. User Checks Request Status
**Endpoint:** `GET /api/requests/api/<request_id>/`

**Example:** `GET /api/requests/api/42/`

**Headers:**
```
Authorization: Bearer USER_TOKEN
```

**Response:**
```json
{
  "id": 42,
  "first_name": "John",
  "last_name": "Doe",
  "status": "completed",
  "payment_status": "paid",
  "has_report": true,
  "created_at": "2024-11-13T12:00:00Z",
  "updated_at": "2024-11-13T14:00:00Z"
}
```

**Connection:** Shows status updated by admin in Step 15

---

### 17. User Views Report Details
**Endpoint:** `GET /api/requests/api/<request_id>/view-report/`

**Example:** `GET /api/requests/api/42/view-report/`

**Headers:**
```
Authorization: Bearer USER_TOKEN
```

**Response:**
```json
{
  "id": 1,
  "request_id": 42,
  "report_type": "basic",
  "status": "completed",
  "findings": {
    "identity_verified": true,
    "criminal_records": false,
    "ssn_verified": true,
    "address_verified": true
  },
  "summary": "Background check completed successfully. No issues found.",
  "completed_at": "2024-11-13T14:00:00Z",
  "pdf_available": true
}
```

**Connection:** Shows report uploaded by admin in Step 14

---

### 18. User Downloads Report PDF
**Endpoint:** `GET /api/requests/api/<request_id>/download-report/`

**Example:** `GET /api/requests/api/42/download-report/`

**Headers:**
```
Authorization: Bearer USER_TOKEN
```

**Response:** PDF file download

**Connection:** Downloads file uploaded by admin in Step 14

---

## PART 7: ADMIN ANALYTICS & MONITORING

### 19. Admin Views All Payments
**Endpoint:** `GET /api/admin/payments/`

**Query Parameters:**
- `user_id=5` - Filter by user
- `status=succeeded` - Filter by status
- `start_date=2024-11-01` - From date
- `end_date=2024-11-30` - To date

**Response:**
```json
{
  "count": 50,
  "total_amount": "1250.00",
  "payments": [
    {
      "id": 1,
      "user": {
        "id": 5,
        "username": "user123",
        "email": "user@example.com"
      },
      "plan": "Basic Plan",
      "amount": "25.00",
      "status": "succeeded",
      "created_at": "2024-11-13T12:30:00Z"
    }
  ]
}
```

**Connection:** Shows payments from Step 8-9

---

### 20. Admin Views Analytics
**Endpoint:** `GET /api/admin/analytics/`

**Response:**
```json
{
  "overview": {
    "total_revenue": "15000.00",
    "active_subscriptions": 150,
    "total_transactions": 500,
    "successful_transactions": 475
  },
  "popular_plans": [
    {
      "id": 1,
      "name": "Basic Plan",
      "subscribers": 85,
      "revenue": "2125.00"
    }
  ],
  "revenue_by_month": [
    {
      "month": "2024-11",
      "revenue": "2500.00",
      "transactions": 100
    }
  ]
}
```

**Connection:** Aggregates data from all plans and payments

---

## COMPLETE ENDPOINT SUMMARY

### ADMIN ENDPOINTS (11 endpoints)

#### Plan Management (4)
1. `POST /api/admin/plans/` - Create plan
2. `GET /api/admin/plans/` - View all plans
3. `PATCH /api/admin/plans/<id>/` - Edit plan
4. `DELETE /api/admin/plans/<id>/` - Delete plan

#### Request Management (5)
5. `GET /api/admin/dashboard/requests/` - View all requests
6. `GET /api/admin/dashboard/requests/<id>/` - View request details
7. `PATCH /api/admin/dashboard/requests/<id>/status/` - Update status
8. `POST /api/admin/dashboard/requests/<id>/notes/` - Add notes
9. `POST /api/admin/reports/upload/` - Upload report PDF

#### Analytics (2)
10. `GET /api/admin/payments/` - View all payments
11. `GET /api/admin/analytics/` - View analytics dashboard

---

### USER ENDPOINTS (9 endpoints)

#### Authentication (1)
1. `POST /api/auth/login/` - User login

#### Plans (1)
2. `GET /api/subscriptions/plans/` - View available plans

#### Request Submission (2)
3. `POST /api/requests/api/` - Submit background check form
4. `GET /api/requests/api/<id>/` - Check request status

#### Payment (2)
5. `POST /api/requests/api/<id>/select-pricing/` - Select plan & create payment
6. `GET /api/requests/api/<id>/confirm-payment/` - Confirm payment (automatic)

#### View Results (3)
7. `GET /api/requests/api/<id>/view-report/` - View report details
8. `GET /api/requests/api/<id>/download-report/` - Download PDF report
9. `GET /api/requests/api/<id>/payment-cancelled/` - Handle cancelled payment

---

## ENDPOINT CONNECTIONS MAP

```
┌─────────────────────────────────────────────────────────────┐
│                     ADMIN CREATES PLANS                      │
│  POST /api/admin/plans/ → Creates plans with pricing        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   USER VIEWS PLANS                          │
│  GET /api/subscriptions/plans/ → Shows created plans        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                 USER SUBMITS FORM                            │
│  POST /api/requests/api/ → Creates request (status:pending) │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│               USER SELECTS PLAN & PAYS                       │
│  POST /api/requests/api/<id>/select-pricing/                │
│  → Uses plan from Step 1, Creates Stripe session            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              PAYMENT CONFIRMED (AUTOMATIC)                   │
│  POST /api/subscriptions/webhook/ (Stripe calls this)       │
│  → Changes status: pending → paid                            │
│  → Creates PaymentHistory record                             │
│  → Admin gets notified                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ADMIN VIEWS PAID REQUESTS                       │
│  GET /api/admin/dashboard/requests/?status=paid             │
│  → Shows requests from Step 3 that are now paid              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          ADMIN UPDATES STATUS TO IN_PROGRESS                 │
│  PATCH /api/admin/dashboard/requests/<id>/status/           │
│  → Changes status: paid → in_progress                        │
│  → User gets notified                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│           ADMIN CHECKS & PROCESSES REQUEST                   │
│  GET /api/admin/dashboard/requests/<id>/                    │
│  POST /api/admin/dashboard/requests/<id>/notes/             │
│  → Admin reviews information and verifies                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ADMIN UPLOADS REPORT PDF                        │
│  POST /api/admin/reports/upload/                            │
│  → Uploads completed report file                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│          ADMIN UPDATES STATUS TO COMPLETED                   │
│  PATCH /api/admin/dashboard/requests/<id>/status/           │
│  → Changes status: in_progress → completed                   │
│  → User gets notified: "Report ready!"                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│            USER CHECKS STATUS & VIEWS REPORT                 │
│  GET /api/requests/api/<id>/ → status: completed            │
│  GET /api/requests/api/<id>/view-report/ → See details      │
│  GET /api/requests/api/<id>/download-report/ → Get PDF      │
│  → Shows report uploaded in Step 10                          │
└─────────────────────────────────────────────────────────────┘
```

---

## STATUS FLOW

```
Request Status Progression:

1. pending       → Initial submission (Step 6)
2. paid          → Payment confirmed (Step 8-9)
3. in_progress   → Admin processing (Step 12)
4. completed     → Report ready (Step 15)

Other possible statuses:
- cancelled      → User cancels
- failed         → Payment failed
- refunded       → Payment refunded
```

---

## TESTING ORDER

1. **Admin creates plans** (Steps 1-4)
2. **User views plans** (Step 5)
3. **User submits form** (Step 6)
4. **User selects plan & pays** (Step 7-9)
5. **Admin views request** (Step 10-11)
6. **Admin updates to in_progress** (Step 12)
7. **Admin uploads report** (Step 14)
8. **Admin updates to completed** (Step 15)
9. **User views/downloads report** (Step 16-18)

---

## KEY CONNECTIONS

**Plan ID flows through:**
- Admin creates (Step 1) → User views (Step 5) → User purchases (Step 7)

**Request ID flows through:**
- User submits (Step 6) → Payment (Step 7-9) → Admin processes (Step 10-15) → User downloads (Step 16-18)

**Notifications trigger at:**
- Payment confirmed (Step 9) → Admin notified
- Status → in_progress (Step 12) → User notified
- Status → completed (Step 15) → User notified

**All endpoints working and connected!**
