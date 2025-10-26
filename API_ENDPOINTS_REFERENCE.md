# Complete API Endpoints Reference

## Base URL
```
Production: https://h2o427-backend-u9bx.onrender.com
Local Dev: http://localhost:8000
```

---

## Subscription Endpoints

### **1. Get All Subscription Plans**
```bash
GET /api/subscriptions/plans/
```
**Authentication:** Not required  
**Description:** Get all available subscription plans

**Response:**
```json
[
  {
    "id": 1,
    "name": "Basic Plan",
    "price": "9.99",
    "billing_cycle": "monthly",
    "max_requests_per_month": 10,
    "description": "Perfect for individuals",
    "stripe_price_id": "price_1234...",
    "features": [...],
    "is_active": true
  }
]
```

---

### **2. Create Checkout Session (Stripe Checkout)**
```bash
POST /api/subscriptions/create-checkout-session/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "plan_id": 2,
  "trial_period_days": 7
}
```

**Authentication:** Required  
**Description:** Create a Stripe Checkout session for subscription purchase

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_...",
  "session_id": "cs_test_a1b2c3...",
  "plan": {
    "id": 2,
    "name": "Professional Plan",
    "price": "29.99"
  }
}
```

---

### **3. Verify Checkout Session**
```bash
GET /api/subscriptions/verify-checkout-session/?session_id=cs_test_a1b2c3...
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Authentication:** Required  
**Description:** Verify a Stripe Checkout session and create subscription

**Response:**
```json
{
  "status": "success",
  "message": "Subscription created successfully",
  "subscription": {
    "id": 1,
    "plan": {...},
    "status": "active",
    "start_date": "2025-10-25T10:00:00Z",
    "end_date": "2025-11-25T10:00:00Z"
  }
}
```

---

### **4. Get User Subscription**
```bash
GET /api/subscriptions/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Authentication:** Required  
**Description:** Get current user's subscription details

**Response:**
```json
{
  "id": 1,
  "plan": {
    "id": 2,
    "name": "Professional Plan",
    "price": "29.99",
    "billing_cycle": "monthly",
    "max_requests_per_month": 50
  },
  "status": "active",
  "start_date": "2025-10-25T10:00:00Z",
  "end_date": "2025-11-25T10:00:00Z",
  "requests_used_this_month": 5,
  "remaining_requests": 45,
  "can_make_request": true
}
```

---

### **5. Create Subscription (Payment Intent Method)**
```bash
POST /api/subscriptions/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "plan_id": 2,
  "payment_method_id": "pm_card_visa",
  "trial_period_days": 7
}
```

**Authentication:** Required  
**Description:** Create subscription using Payment Intent (advanced method)

**Response:**
```json
{
  "subscription": {
    "id": 1,
    "plan": {...},
    "status": "active"
  },
  "client_secret": "pi_3N1X...secret",
  "stripe_subscription_id": "sub_1N1X..."
}
```

---

### **6. Update Subscription Plan**
```bash
PATCH /api/subscriptions/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "plan_id": 3,
  "prorate": true
}
```

**Authentication:** Required  
**Description:** Upgrade or downgrade subscription plan

**Response:**
```json
{
  "message": "Subscription updated successfully",
  "subscription": {
    "plan": {
      "name": "Enterprise Plan",
      "price": "99.99"
    },
    "status": "active"
  }
}
```

---

### **7. Cancel Subscription**
```bash
DELETE /api/subscriptions/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "cancel_at_period_end": true
}
```

**Authentication:** Required  
**Description:** Cancel subscription (immediately or at period end)

**Response:**
```json
{
  "message": "Subscription will be canceled at the end of the billing period",
  "subscription": {
    "status": "active",
    "end_date": "2025-11-25T10:00:00Z"
  }
}
```

---

### **8. Get Subscription Usage**
```bash
GET /api/subscriptions/usage/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Authentication:** Required  
**Description:** Get current subscription usage statistics

**Response:**
```json
{
  "current_plan": {
    "name": "Professional Plan",
    "price": "29.99"
  },
  "requests_used_this_month": 15,
  "requests_remaining": 35,
  "max_requests_per_month": 50,
  "can_make_request": true,
  "subscription_status": "active",
  "next_billing_date": "2025-11-25T10:00:00Z"
}
```

---

### **9. Get Payment History**
```bash
GET /api/subscriptions/payment-history/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Authentication:** Required  
**Description:** Get user's payment history

**Response:**
```json
[
  {
    "id": 1,
    "amount": "29.99",
    "currency": "USD",
    "status": "succeeded",
    "description": "Subscription to Professional Plan",
    "created_at": "2025-10-25T10:00:00Z",
    "stripe_payment_intent_id": "pi_3N1X..."
  }
]
```

---

### **10. Stripe Webhook**
```bash
POST /api/subscriptions/webhook/
Content-Type: application/json
Stripe-Signature: <signature>
```

**Authentication:** Stripe signature verification  
**Description:** Handle Stripe webhook events (internal use)

---

### **11. Admin Subscription Stats**
```bash
GET /api/subscriptions/admin/stats/
Authorization: Bearer ADMIN_ACCESS_TOKEN
```

**Authentication:** Admin only  
**Description:** Get subscription statistics for admin dashboard

**Response:**
```json
{
  "total_subscribers": 150,
  "active_subscribers": 120,
  "total_revenue": 4499.85,
  "monthly_revenue": 899.70,
  "most_popular_plan": {
    "id": 2,
    "name": "Professional Plan"
  },
  "recent_payments": [...]
}
```

---

## 🔐 Authentication Endpoints

### **1. Register**
```bash
POST /api/auth/register/
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "phone_number": "+1234567890",
  "full_name": "John Doe",
  "password": "SecurePass123!"
}
```

---

### **2. Login**
```bash
POST /api/auth/login/
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI..."
  },
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

---

### **3. Refresh Token**
```bash
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI..."
}
```

---

### **4. Logout**
```bash
POST /api/auth/logout/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

### **5. Forgot Password**
```bash
POST /api/auth/forgot-password/
Content-Type: application/json

{
  "email": "john@example.com"
}
```

---

### **6. Reset Password**
```bash
POST /api/auth/reset-password/
Content-Type: application/json

{
  "uid": "MQ",
  "token": "c5q8vy-abc123...",
  "new_password": "NewSecurePass123!"
}
```

---

### **7. Change Password**
```bash
POST /api/auth/change-password/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "old_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

---

### **8. Get User Profile**
```bash
GET /api/auth/profile/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

### **9. Update User Profile**
```bash
PATCH /api/auth/profile/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "full_name": "John Smith",
  "phone_number": "+1234567890"
}
```

---

### **10. Upload Profile Picture**
```bash
POST /api/auth/profile/picture/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data

profile_picture: <file>
```

---

## 📋 Background Check Request Endpoints

### **1. Create Background Check Request**
```bash
POST /api/requests/api/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "name": "Jane Smith",
  "dob": "1990-05-15",
  "city": "New York",
  "state": "NY",
  "email": "jane.smith@example.com",
  "phone_number": "+1234567890"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Jane Smith",
  "status": "Pending",
  "created_at": "2025-10-25T10:30:00Z",
  "requests_remaining": 49
}
```

---

### **2. Get All User Requests**
```bash
GET /api/requests/api/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

### **3. Get Request by ID**
```bash
GET /api/requests/api/{id}/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

### **4. Update Request Status (Admin)**
```bash
PATCH /api/requests/api/{id}/
Authorization: Bearer ADMIN_ACCESS_TOKEN
Content-Type: application/json

{
  "status": "Completed",
  "report_file": "path/to/report.pdf"
}
```

---

### **5. Delete Request**
```bash
DELETE /api/requests/api/{id}/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## 🔔 Notification Endpoints

### **1. Get All Notifications**
```bash
GET /api/notifications/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

### **2. Mark Notification as Read**
```bash
POST /api/notifications/{id}/mark-as-read/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

### **3. Mark All as Read**
```bash
POST /api/notifications/mark-all-as-read/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

### **4. Delete Notification**
```bash
DELETE /api/notifications/{id}/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## 👨‍💼 Admin Dashboard Endpoints

### **1. Get Dashboard Stats**
```bash
GET /api/admin/dashboard/
Authorization: Bearer ADMIN_ACCESS_TOKEN
```

**Response:**
```json
{
  "total_users": 500,
  "active_subscriptions": 250,
  "pending_requests": 45,
  "completed_requests": 1200,
  "total_revenue": 12499.75,
  "monthly_revenue": 2999.85
}
```

---

### **2. Get All Users (Admin)**
```bash
GET /api/admin/users/
Authorization: Bearer ADMIN_ACCESS_TOKEN
```

---

### **3. Get All Requests (Admin)**
```bash
GET /api/admin/requests/
Authorization: Bearer ADMIN_ACCESS_TOKEN
```

---

### **4. Update Request Status (Admin)**
```bash
PATCH /api/admin/requests/{id}/
Authorization: Bearer ADMIN_ACCESS_TOKEN
Content-Type: application/json

{
  "status": "Completed",
  "notes": "Background check completed successfully"
}
```

---

## 🎯 Quick Reference - Most Used Endpoints

| Action | Method | Endpoint |
|--------|--------|----------|
| Register | POST | `/api/auth/register/` |
| Login | POST | `/api/auth/login/` |
| Get Plans | GET | `/api/subscriptions/plans/` |
| Create Checkout | POST | `/api/subscriptions/create-checkout-session/` |
| Verify Checkout | GET | `/api/subscriptions/verify-checkout-session/?session_id=...` |
| Get Subscription | GET | `/api/subscriptions/` |
| Check Usage | GET | `/api/subscriptions/usage/` |
| Create Request | POST | `/api/requests/api/` |
| Get Requests | GET | `/api/requests/api/` |
| Get Notifications | GET | `/api/notifications/` |

---

## 🔧 Testing with cURL

### Create Checkout Session Example:
```bash
curl -X POST https://h2o427-backend-u9bx.onrender.com/api/subscriptions/create-checkout-session/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 2,
    "trial_period_days": 7
  }'
```

### Get Subscription Example:
```bash
curl -X GET https://h2o427-backend-u9bx.onrender.com/api/subscriptions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 📱 Error Codes

| Status Code | Meaning |
|-------------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

---

## ✅ Common Response Formats

### Success Response:
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {...}
}
```

### Error Response:
```json
{
  "error": "Error message here",
  "detail": "Detailed error information"
}
```

---

## 🎉 Need Help?

- 📚 Full Documentation: `/swagger/` or `/redoc/`
- 📧 Support: support@backgroundcheck.com
- 🌐 API Status: All endpoints operational

**Happy Coding! 🚀**
