# Pay-Per-Report System - Complete User Flow

## Overview

The system has been modified to implement a **pay-after-submission** flow where users:
1. Login
2. Submit background check request form
3. Choose between $25 (Basic) or $50 (Premium) report
4. Complete payment via Stripe Checkout
5. Receive their report once processing is complete

No upfront subscription is required.

---

## Complete User Flow

### Step 1: User Login

**Endpoint:** `POST /api/auth/login/`

**Request:**
```json
{
    "email": "user@example.com",
    "password": "Password123!"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": 1,
        "username": "johndoe",
        "email": "user@example.com"
    }
}
```

Save the `access` token for subsequent requests.

---

### Step 2: Submit Background Check Request

**Endpoint:** `POST /api/requests/api/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request:**
```json
{
    "name": "John Smith",
    "email": "john.smith@example.com",
    "phone_number": "+1234567890",
    "dob": "1990-05-15",
    "city": "New York",
    "state": "NY"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Background check request submitted successfully",
    "request": {
        "id": 1,
        "name": "John Smith",
        "email": "john.smith@example.com",
        "phone_number": "+1234567890",
        "dob": "1990-05-15",
        "city": "New York",
        "state": "NY",
        "status": "Pending",
        "payment_status": "payment_pending",
        "report_type": null,
        "payment_amount": null,
        "created_at": "2025-11-10T10:30:00Z"
    },
    "next_step": {
        "action": "select_payment",
        "url": "/api/requests/api/1/select-pricing/",
        "message": "Please select your report type ($25 or $50) and proceed to payment",
        "pricing_options": {
            "basic": {
                "price": 25,
                "features": "Identity verification, criminal history check"
            },
            "premium": {
                "price": 50,
                "features": "All basic features + employment & education verification"
            }
        }
    }
}
```

**Key Changes:**
- No subscription checks required
- Request is created with `payment_status = 'payment_pending'`
- User is directed to payment selection

---

### Step 3: View Pricing Options (Optional)

**Endpoint:** `GET /api/requests/api/pricing-options/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
    "pricing_options": [
        {
            "type": "basic",
            "price": 25.00,
            "name": "Basic Report",
            "description": "Essential background check",
            "features": [
                "Identity Verification",
                "SSN Trace",
                "National Criminal Search",
                "Sex Offender Registry",
                "Address History"
            ],
            "delivery": "2-3 business days"
        },
        {
            "type": "premium",
            "price": 50.00,
            "name": "Premium Report",
            "description": "Comprehensive background check",
            "features": [
                "All Basic Report features",
                "Employment Verification",
                "Education Verification",
                "Unlimited County Search",
                "Priority Processing",
                "Dedicated Support"
            ],
            "delivery": "1-2 business days"
        }
    ]
}
```

---

### Step 4: Select Report Type and Create Payment

**Endpoint:** `POST /api/requests/api/{request_id}/select-pricing/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body (IMPORTANT - use exact field name):**
```json
{
    "report_type": "basic"
}
```

OR for Premium:

```json
{
    "report_type": "premium"
}
```

**⚠️ Common Error:** Make sure you use `"report_type"` NOT `"type"` in your request body!

**Response:**
```json
{
    "success": true,
    "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_a1b2c3d4e5f6...",
    "session_id": "cs_test_a1b2c3d4e5f6...",
    "report_type": "basic",
    "amount": 25.00,
    "message": "Redirect user to checkout_url to complete payment"
}
```

**Frontend Action:**
```javascript
// Redirect user to Stripe Checkout
window.location.href = data.checkout_url;
```

---

### Step 5: User Completes Payment on Stripe

User is redirected to Stripe's official checkout page where they:
1. Enter card details
2. Complete payment
3. Are automatically redirected back

**Test Card Details (for testing):**
- Card Number: `4242 4242 4242 4242`
- Expiry: Any future date (e.g., `12/25`)
- CVC: Any 3 digits (e.g., `123`)
- ZIP: Any 5 digits (e.g., `12345`)

---

### Step 6: Automatic Payment Confirmation

After successful payment, Stripe redirects to:

**Endpoint:** `GET /api/requests/api/{request_id}/confirm-payment/?session_id={SESSION_ID}`

This endpoint is called automatically by Stripe. The backend:
1. Verifies payment with Stripe
2. Updates request: `payment_status = 'payment_completed'`
3. Records payment details
4. Begins processing the background check

**Response:**
```json
{
    "success": true,
    "message": "Payment confirmed! Your background check is being processed.",
    "request": {
        "id": 1,
        "name": "John Smith",
        "status": "Pending",
        "payment_status": "payment_completed",
        "report_type": "basic",
        "payment_amount": 25.00,
        "payment_date": "2025-11-10T10:35:00Z"
    },
    "next_steps": {
        "message": "You will be notified when your report is ready",
        "check_status_url": "/api/requests/api/1/"
    }
}
```

---

### Step 7: Check Request Status

**Endpoint:** `GET /api/requests/api/{request_id}/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
    "id": 1,
    "user": 1,
    "user_name": "johndoe",
    "user_email": "user@example.com",
    "name": "John Smith",
    "dob": "1990-05-15",
    "city": "New York",
    "state": "NY",
    "email": "john.smith@example.com",
    "phone_number": "+1234567890",
    "status": "In Progress",
    "payment_status": "payment_completed",
    "report_type": "basic",
    "payment_amount": "25.00",
    "payment_date": "2025-11-10T10:35:00Z",
    "created_at": "2025-11-10T10:30:00Z",
    "updated_at": "2025-11-10T10:35:00Z",
    "days_since_created": 0,
    "report_price": 25.00
}
```

---

### Step 8: View Completed Report

Once status changes to "Completed":

**Endpoint:** `GET /api/requests/api/{request_id}/view-report/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:** Complete report details with all verification sections

---

### Step 9: Download PDF Report

**Endpoint:** `GET /api/requests/api/{request_id}/download-report/`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
    "success": true,
    "report": {
        "id": 1,
        "download_url": "http://localhost:8000/media/reports/report_1.pdf",
        "filename": "report_1.pdf",
        "generated_at": "2025-11-10T12:00:00Z",
        "file_size_mb": "1.50 MB"
    },
    "request": {
        "id": 1,
        "name": "John Smith",
        "status": "Completed"
    }
}
```

---

## Payment Cancellation Handling

If user cancels payment on Stripe checkout page:

**Endpoint:** `GET /api/requests/api/{request_id}/payment-cancelled/`

**Response:**
```json
{
    "message": "Payment was cancelled",
    "request_id": 1,
    "retry_url": "/api/requests/api/1/select-pricing/",
    "note": "You can try again by selecting a report type"
}
```

User can retry payment by going back to the select-pricing endpoint.

---

## API Endpoints Summary

### User Flow Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login/` | User login |
| POST | `/api/requests/api/` | Submit background check request |
| GET | `/api/requests/api/pricing-options/` | View pricing options |
| POST | `/api/requests/api/{id}/select-pricing/` | Select report type and create payment |
| GET | `/api/requests/api/{id}/confirm-payment/` | Confirm payment (automatic) |
| GET | `/api/requests/api/{id}/payment-cancelled/` | Handle cancelled payment |
| GET | `/api/requests/api/{id}/` | Check request status |
| GET | `/api/requests/api/{id}/view-report/` | View completed report details |
| GET | `/api/requests/api/{id}/download-report/` | Download PDF report |

---

## Testing in Postman

### Complete Test Flow:

1. **Login:**
   ```
   POST http://localhost:8000/api/auth/login/
   Body: {"email": "user@example.com", "password": "password"}
   ```

2. **Submit Request:**
   ```
   POST http://localhost:8000/api/requests/api/
   Headers: Authorization: Bearer {token}
   Body: {name, email, phone_number, dob, city, state}
   ```

3. **View Pricing:**
   ```
   GET http://localhost:8000/api/requests/api/pricing-options/
   ```

4. **Select Pricing:**
   ```
   POST http://localhost:8000/api/requests/api/1/select-pricing/
   Headers: Authorization: Bearer {token}
   Body: {"report_type": "basic"}
   ```

5. **Copy checkout_url from response and open in browser**

6. **Complete payment with test card: 4242 4242 4242 4242**

7. **After redirect, check status:**
   ```
   GET http://localhost:8000/api/requests/api/1/
   Headers: Authorization: Bearer {token}
   ```

---
