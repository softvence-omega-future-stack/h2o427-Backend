# Complete User Journey: Purchase Plan & Submit Background Check

## Overview
This guide shows the complete process for a new user to:
1. Register an account
2. View available plans
3. Purchase reports
4. Submit a background check request

---

## API Endpoints

### Base URL
```
http://127.0.0.1:8000/api/
```

### Available Endpoints
1. `POST /auth/register/` - Create account
2. `POST /auth/login/` - Get authentication token
3. `GET /subscriptions/plans/` - View available plans  
4. `POST /subscriptions/purchase-report/` - Purchase reports
5. `POST /subscriptions/confirm-payment/` - Confirm payment
6. `GET /subscriptions/usage/` - Check available reports
7. `POST /requests/` - Submit background check request

---

## Step-by-Step Process

### Step 1: Register New User

**Endpoint:** `POST /api/auth/register/`

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
  }'
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "token": "your_auth_token_here",
  "message": "User registered successfully"
}
```

**Save the token** - you'll need it for authenticated requests!

---

### Step 2: Login (if already registered)

**Endpoint:** `POST /api/auth/login/`

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_doe",
    "password": "SecurePass123!"
  }'
```

**Response:**
```json
{
  "token": "your_auth_token_here",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com"
  }
}
```

---

### Step 3: View Available Plans

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
    "description": "Identity Verification\nSSN Trace\nNational Criminal Search\nSex Offender Registry",
    "feature_list": [
      "Identity Verification",
      "SSN Trace",
      "National Criminal Search",
      "Sex Offender Registry",
      "Standard Support",
      "API Access"
    ],
    "is_active": true
  },
  {
    "id": 2,
    "name": "Premium Plan",
    "plan_type": "premium",
    "price_per_report": "50.00",
    "description": "All Basic Plan features plus:\nEmployment History Verification\nEducation Verification\nUnlimited County Criminal Search\nPriority Support",
    "feature_list": [
      "Identity Verification",
      "SSN Trace",
      "National Criminal Search",
      "Sex Offender Registry",
      "Employment History Verification",
      "Education Verification",
      "Unlimited County Criminal Search",
      "Priority Support",
      "API Access"
    ],
    "is_active": true
  }
]
```

---

### Step 4: Purchase Reports

**Endpoint:** `POST /api/subscriptions/purchase-report/`

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/subscriptions/purchase-report/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your_auth_token_here" \
  -d '{
    "plan_id": 1,
    "quantity": 1
  }'
```

**Request Body Parameters:**
- `plan_id` (required): ID of the plan to purchase (1 for Basic, 2 for Premium)
- `quantity` (optional): Number of reports to purchase (default: 1)

**Response:**
```json
{
  "client_secret": "pi_3Abc123_secret_xyz789",
  "payment_intent_id": "pi_3Abc123DefGhi456",
  "amount": 25.00,
  "quantity": 1,
  "plan": "Basic Plan",
  "plan_price": 25.00
}
```

**Important:** Save the `payment_intent_id` and `client_secret` for the next step!

---

### Step 5: Complete Payment (Frontend Integration)

Use Stripe's frontend SDK to complete the payment:

**HTML/JavaScript Example:**
```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://js.stripe.com/v3/"></script>
</head>
<body>
    <form id="payment-form">
        <div id="card-element"></div>
        <button type="submit">Pay Now</button>
        <div id="error-message"></div>
    </form>

    <script>
        // Initialize Stripe
        const stripe = Stripe('your_stripe_publishable_key');
        const elements = stripe.elements();
        const cardElement = elements.create('card');
        cardElement.mount('#card-element');

        // Handle form submission
        const form = document.getElementById('payment-form');
        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            // Get client secret from Step 4 response
            const clientSecret = 'pi_3Abc123_secret_xyz789';

            // Confirm payment
            const {error, paymentIntent} = await stripe.confirmCardPayment(
                clientSecret,
                {
                    payment_method: {
                        card: cardElement,
                        billing_details: {
                            name: 'John Doe',
                            email: 'john@example.com'
                        }
                    }
                }
            );

            if (error) {
                document.getElementById('error-message').textContent = error.message;
            } else if (paymentIntent.status === 'succeeded') {
                // Payment successful! Confirm with backend
                confirmPayment(paymentIntent.id);
            }
        });

        async function confirmPayment(paymentIntentId) {
            const response = await fetch('http://127.0.0.1:8000/api/subscriptions/confirm-payment/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Token your_auth_token_here'
                },
                body: JSON.stringify({
                    payment_intent_id: paymentIntentId
                })
            });

            const result = await response.json();
            console.log('Payment confirmed:', result);
            alert('Successfully purchased reports!');
        }
    </script>
</body>
</html>
```

---

### Step 6: Confirm Payment

**Endpoint:** `POST /api/subscriptions/confirm-payment/`

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/subscriptions/confirm-payment/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your_auth_token_here" \
  -d '{
    "payment_intent_id": "pi_3Abc123DefGhi456"
  }'
```

**Response:**
```json
{
  "message": "Successfully purchased 1 report",
  "subscription": {
    "id": 1,
    "user": 1,
    "plan": {
      "id": 1,
      "name": "Basic Plan",
      "price_per_report": "25.00"
    },
    "free_trial_used": false,
    "total_reports_purchased": 1,
    "total_reports_used": 0,
    "available_reports": 1,
    "can_make_request": true,
    "can_use_free_trial": true
  }
}
```

---

### Step 7: Check Available Reports

**Endpoint:** `GET /api/subscriptions/usage/`

**Request:**
```bash
curl -X GET http://127.0.0.1:8000/api/subscriptions/usage/ \
  -H "Authorization: Token your_auth_token_here"
```

**Response:**
```json
{
  "current_plan": {
    "id": 1,
    "name": "Basic Plan",
    "price_per_report": "25.00"
  },
  "total_reports_purchased": 1,
  "total_reports_used": 0,
  "available_reports": 1,
  "free_trial_used": false,
  "can_use_free_trial": true,
  "can_make_request": true
}
```

---

### Step 8: Submit Background Check Request

**Endpoint:** `POST /api/requests/`

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/api/requests/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your_auth_token_here" \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1990-05-15",
    "ssn": "123-45-6789",
    "email": "jane.smith@example.com",
    "phone": "+1234567890",
    "address": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip_code": "10001",
    "country": "USA"
  }'
```

**Response:**
```json
{
  "id": 1,
  "request_number": "REQ-2025-001",
  "status": "pending",
  "submitted_by": "john_doe",
  "subject": {
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1990-05-15"
  },
  "created_at": "2025-11-09T10:30:00Z",
  "message": "Background check request submitted successfully"
}
```

---

## Complete Python Example

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

# Step 1: Register
def register_user():
    url = f"{BASE_URL}/auth/register/"
    data = {
        "username": "john_doe",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "phone_number": "+1234567890"
    }
    response = requests.post(url, json=data)
    return response.json()['token']

# Step 2: View Plans
def get_plans():
    url = f"{BASE_URL}/subscriptions/plans/"
    response = requests.get(url)
    return response.json()

# Step 3: Purchase Report
def purchase_report(token, plan_id, quantity=1):
    url = f"{BASE_URL}/subscriptions/purchase-report/"
    headers = {"Authorization": f"Token {token}"}
    data = {"plan_id": plan_id, "quantity": quantity}
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Step 4: Confirm Payment (after Stripe payment)
def confirm_payment(token, payment_intent_id):
    url = f"{BASE_URL}/subscriptions/confirm-payment/"
    headers = {"Authorization": f"Token {token}"}
    data = {"payment_intent_id": payment_intent_id}
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Step 5: Check Usage
def check_usage(token):
    url = f"{BASE_URL}/subscriptions/usage/"
    headers = {"Authorization": f"Token {token}"}
    response = requests.get(url, headers=headers)
    return response.json()

# Step 6: Submit Background Check
def submit_request(token):
    url = f"{BASE_URL}/requests/"
    headers = {"Authorization": f"Token {token}"}
    data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "date_of_birth": "1990-05-15",
        "ssn": "123-45-6789",
        "email": "jane.smith@example.com",
        "phone": "+1234567890",
        "address": "123 Main St",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
        "country": "USA"
    }
    response = requests.post(url, json=data, headers=headers)
    return response.json()

# Main flow
if __name__ == "__main__":
    # 1. Register and get token
    token = register_user()
    print(f"Registered! Token: {token}")
    
    # 2. View plans
    plans = get_plans()
    print(f"Available plans: {len(plans)}")
    
    # 3. Purchase report (Basic Plan)
    purchase = purchase_report(token, plan_id=1, quantity=1)
    print(f"Purchase initiated: {purchase['payment_intent_id']}")
    
    # 4. (Complete Stripe payment here)
    # payment_intent_id = purchase['payment_intent_id']
    
    # 5. Confirm payment
    # confirm = confirm_payment(token, payment_intent_id)
    # print(f"Payment confirmed: {confirm['message']}")
    
    # 6. Check usage
    usage = check_usage(token)
    print(f"Available reports: {usage['available_reports']}")
    
    # 7. Submit request
    request = submit_request(token)
    print(f"Request submitted: {request['request_number']}")
```

---

## Free Trial Flow

New users get 1 free search! They can skip the purchase step:

```bash
# 1. Register
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"new_user","email":"user@example.com","password":"Pass123!"}'

# 2. Submit request directly (uses free trial)
curl -X POST http://127.0.0.1:8000/api/requests/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token your_token" \
  -d '{
    "first_name":"Jane",
    "last_name":"Doe",
    "date_of_birth":"1990-01-01",
    "ssn":"123-45-6789"
  }'
```

---

## Error Handling

### Common Errors

**401 Unauthorized:**
```json
{
  "detail": "Authentication credentials were not provided."
}
```
Solution: Include `Authorization: Token your_token` header

**400 Bad Request - No Reports Available:**
```json
{
  "error": "No reports available. Please purchase more reports."
}
```
Solution: Purchase more reports first

**404 Plan Not Found:**
```json
{
  "error": "Plan not found"
}
```
Solution: Use correct plan_id (1 or 2)

---

## Testing with Stripe

### Test Card Numbers

```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
3D Secure: 4000 0025 0000 3155
```

Use any future expiration date and any 3-digit CVC.

---

## Summary

Complete flow:
1. Register → Get Token
2. View Plans → Choose Plan
3. Purchase Report → Get Payment Intent
4. Complete Payment → Use Stripe
5. Confirm Payment → Add Reports
6. Submit Request → Process Background Check

That's it! The user now has a complete end-to-end flow from registration to submitting background checks.
