# 📋 How to Subscribe to a Plan - User Guide

## 🎯 Complete Step-by-Step Subscription Guide

---

## 📱 Method 1: Using API (For Mobile/Web App Integration)

### **Step 1: Register & Login**

**1.1 Register a New Account:**
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

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

**1.2 Login to Get Access Token:**
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

### **Step 2: Browse Available Plans**

```bash
GET /api/subscriptions/plans/
```

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
    "features": [
      "Basic identity verification",
      "10 background checks per month",
      "Standard support"
    ],
    "is_active": true
  },
  {
    "id": 2,
    "name": "Professional Plan",
    "price": "29.99",
    "billing_cycle": "monthly",
    "max_requests_per_month": 50,
    "description": "For small businesses",
    "stripe_price_id": "price_5678...",
    "features": [
      "Full criminal records search",
      "50 background checks per month",
      "Employment verification",
      "Priority support"
    ],
    "is_active": true
  },
  {
    "id": 3,
    "name": "Enterprise Plan",
    "price": "99.99",
    "billing_cycle": "monthly",
    "max_requests_per_month": 999999,
    "description": "For large organizations",
    "stripe_price_id": "price_9012...",
    "features": [
      "Unlimited background checks",
      "All verification types",
      "API access",
      "Dedicated support",
      "Custom reports"
    ],
    "is_active": true
  }
]
```

---

### **Step 3: Create Checkout Session**

**Option A: Using Stripe Checkout (Recommended - Easiest)**

```bash
POST https://h2o427-backend-u9bx.onrender.com/api/subscriptions/create-checkout-session/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "plan_id": 2,
  "trial_period_days": 7
}
```

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

**What to do next:**
1. Open the `checkout_url` in a browser or WebView
2. User enters payment information on Stripe's secure page
3. After payment, user is redirected to success URL
4. Subscription is automatically created

---

**Option B: Using Payment Intent (Advanced - More Control)**

```bash
POST https://h2o427-backend-u9bx.onrender.com/api/subscriptions/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "plan_id": 2,
  "payment_method_id": "pm_card_visa",
  "trial_period_days": 7
}
```

**Response:**
```json
{
  "subscription": {
    "id": 1,
    "plan": {
      "name": "Professional Plan",
      "price": "29.99"
    },
    "status": "active",
    "start_date": "2025-10-25T10:00:00Z",
    "end_date": "2025-11-25T10:00:00Z",
    "trial_end": "2025-11-01T10:00:00Z",
    "requests_used_this_month": 0,
    "remaining_requests": 50
  },
  "client_secret": "pi_3N1X...secret",
  "stripe_subscription_id": "sub_1N1X..."
}
```

---

### **Step 4: Verify Subscription**

**After successful payment (redirect from Stripe):**

```bash
GET https://h2o427-backend-u9bx.onrender.com/api/subscriptions/verify-checkout-session/?session_id=cs_test_a1b2c3...
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
{
  "status": "success",
  "message": "Subscription created successfully",
  "subscription": {
    "id": 1,
    "plan": {
      "id": 2,
      "name": "Professional Plan",
      "price": "29.99",
      "max_requests_per_month": 50
    },
    "status": "active",
    "start_date": "2025-10-25T10:00:00Z",
    "end_date": "2025-11-25T10:00:00Z",
    "requests_used_this_month": 0,
    "remaining_requests": 50,
    "can_make_request": true
  }
}
```

---

### **Step 5: Check Subscription Status**

```bash
GET https://h2o427-backend-u9bx.onrender.com/api/subscriptions/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

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
  "trial_end": null,
  "requests_used_this_month": 5,
  "remaining_requests": 45,
  "can_make_request": true,
  "stripe_subscription_id": "sub_1N1X...",
  "stripe_customer_id": "cus_1N1X..."
}
```

---

### **Step 6: Use Your Subscription**

**Make a background check request:**

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

## 🌐 Method 2: Using Web Interface (Browser)

### **Step 1: Visit the Website**
```
https://h2o427-backend-u9bx.onrender.com/
```

### **Step 2: Register/Login**
1. Click "Register" or "Sign Up"
2. Fill in your details
3. Verify your email/phone
4. Login with your credentials

### **Step 3: View Plans**
1. Navigate to **"Pricing"** or **"Plans"** page
2. Compare available plans:
   - Basic Plan ($9.99/month)
   - Professional Plan ($29.99/month)
   - Enterprise Plan ($99.99/month)

### **Step 4: Select a Plan**
1. Click **"Choose Plan"** or **"Subscribe"** button
2. Review plan features
3. Click **"Proceed to Payment"**

### **Step 5: Complete Payment**
1. You'll be redirected to **Stripe Checkout**
2. Enter your card information:
   - Card number
   - Expiration date (MM/YY)
   - CVC
   - ZIP code
3. Click **"Subscribe"**

### **Step 6: Confirmation**
1. You'll see a success page
2. Check your email for confirmation
3. Subscription is now active!

### **Step 7: Access Your Dashboard**
1. Go to **"My Subscription"** or **"Dashboard"**
2. View:
   - Current plan
   - Usage statistics
   - Remaining requests
   - Next billing date

---

## 📊 Managing Your Subscription

### **Check Usage:**
```bash
GET /api/subscriptions/usage/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

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

### **Upgrade/Downgrade Plan:**
```bash
PATCH /api/subscriptions/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "plan_id": 3,
  "prorate": true
}
```

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

### **Cancel Subscription:**

**Option 1: Cancel at Period End (Recommended)**
```bash
DELETE /api/subscriptions/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "cancel_at_period_end": true
}
```

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

**Option 2: Cancel Immediately**
```bash
DELETE /api/subscriptions/
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "cancel_at_period_end": false
}
```

---

### **View Payment History:**
```bash
GET /api/subscriptions/payment-history/
Authorization: Bearer YOUR_ACCESS_TOKEN
```

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
  },
  {
    "id": 2,
    "amount": "29.99",
    "currency": "USD",
    "status": "succeeded",
    "description": "Monthly renewal",
    "created_at": "2025-09-25T10:00:00Z"
  }
]
```

---

## 🔧 Testing with Stripe Test Cards

Use these test card numbers in **test mode**:

| Card Number | Description | Expected Result |
|-------------|-------------|-----------------|
| `4242 4242 4242 4242` | Visa | Success |
| `4000 0025 0000 3155` | Visa (3D Secure) | Requires authentication |
| `4000 0000 0000 9995` | Visa | Declined |
| `5555 5555 5555 4444` | Mastercard | Success |

**For all test cards:**
- Expiration: Any future date (e.g., 12/34)
- CVC: Any 3 digits (e.g., 123)
- ZIP: Any 5 digits (e.g., 12345)

---

## 🎯 Complete Frontend Integration Example

### **React/JavaScript Example:**

```javascript
// 1. Fetch available plans
async function getPlans() {
  const response = await fetch('https://h2o427-backend-u9bx.onrender.com/api/subscriptions/plans/');
  const plans = await response.json();
  return plans;
}

// 2. Create checkout session
async function subscribe(planId, accessToken) {
  const response = await fetch(
    'https://h2o427-backend-u9bx.onrender.com/api/subscriptions/create-checkout-session/',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        plan_id: planId,
        trial_period_days: 7
      })
    }
  );
  
  const data = await response.json();
  
  // Redirect to Stripe Checkout
  window.location.href = data.checkout_url;
}

// 3. Verify subscription after redirect
async function verifySubscription(sessionId, accessToken) {
  const response = await fetch(
    `https://h2o427-backend-u9bx.onrender.com/api/subscriptions/verify-checkout-session/?session_id=${sessionId}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  const data = await response.json();
  return data;
}

// 4. Check subscription status
async function getSubscription(accessToken) {
  const response = await fetch(
    'https://h2o427-backend-u9bx.onrender.com/api/subscriptions/',
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );
  
  const subscription = await response.json();
  return subscription;
}
```

---

## ✅ Summary - Quick Steps

1. **Register** → Create an account
2. **Login** → Get access token
3. **Browse Plans** → View available subscription plans
4. **Select Plan** → Choose the plan that fits your needs
5. **Payment** → Complete payment via Stripe Checkout
6. **Verify** → Confirm subscription creation
7. **Use Service** → Start making background check requests!

---

## 🆘 Troubleshooting

### **"User already has an active subscription"**
- You can only have one active subscription at a time
- Cancel current subscription first, or upgrade/downgrade instead

### **"Payment failed"**
- Check card details
- Ensure sufficient funds
- Try a different card
- Contact your bank

### **"No subscription found"**
- You haven't subscribed yet
- Your subscription may have been canceled
- Check payment status

### **"Request limit reached"**
- Upgrade to a higher plan
- Wait for monthly reset
- Contact support for custom limits

---

## 📞 Support

Need help? Contact us:
- 📧 Email: support@backgroundcheck.com
- 📱 Phone: +1-800-123-4567
- 💬 Live Chat: Available in dashboard

---

## 🎉 You're All Set!

Once subscribed, you can:
✅ Make background check requests  
✅ View detailed reports  
✅ Track usage  
✅ Manage your subscription  
✅ Access API endpoints  

**Happy checking! 🚀**
