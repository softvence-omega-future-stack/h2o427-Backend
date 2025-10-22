// ==========================================
// FRONTEND INTEGRATION EXAMPLE
// React + Stripe Elements
// ==========================================

import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';

// Initialize Stripe with your PUBLISHABLE key
const stripePromise = loadStripe('pk_test_51SJZg4AH6r5jNzNwuFyHUFFE0NJEcV17D2FZXEAYApasqgrIaPi44n1gT2sBKDq3RNPbP63gCRdvpSCUgJt5VsWW00x7PIkSx6');

// ==========================================
// STEP 1: Display Available Plans
// ==========================================
function PlanSelection({ onSelectPlan }) {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch available plans (no auth needed)
    fetch('http://127.0.0.1:8000/api/subscriptions/plans/')
      .then(res => res.json())
      .then(data => {
        setPlans(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching plans:', err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div>Loading plans...</div>;

  return (
    <div className="plans-container">
      <h2>Choose Your Plan</h2>
      <div className="plans-grid">
        {plans.map(plan => (
          <div key={plan.id} className="plan-card">
            <h3>{plan.name}</h3>
            <div className="price">
              ${plan.price}
              <span>/{plan.billing_cycle}</span>
            </div>
            <ul className="features">
              {plan.feature_list.map((feature, idx) => (
                <li key={idx}>✓ {feature}</li>
              ))}
            </ul>
            <button 
              className="btn-subscribe"
              onClick={() => onSelectPlan(plan)}
            >
              Subscribe Now
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ==========================================
// STEP 2: Payment Form
// ==========================================
function CheckoutForm({ selectedPlan, jwtToken }) {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    
    if (!stripe || !elements) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Create payment method using Stripe.js
      const { error: pmError, paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
        card: elements.getElement(CardElement),
        billing_details: {
          name: 'John Doe', // Get from user profile
          email: 'john@example.com', // Get from user profile
        },
      });

      if (pmError) {
        setError(pmError.message);
        setLoading(false);
        return;
      }

      console.log('Payment method created:', paymentMethod.id);

      // 2. Send payment method to backend to create subscription
      const response = await fetch('http://127.0.0.1:8000/api/subscriptions/subscription/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${jwtToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          plan_id: selectedPlan.id,
          payment_method_id: paymentMethod.id,
          trial_period_days: 0, // Change to 7 for trial
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Failed to create subscription');
      }

      console.log('Subscription created:', result);

      // 3. If payment requires confirmation (3D Secure)
      if (result.client_secret) {
        const { error: confirmError } = await stripe.confirmCardPayment(
          result.client_secret
        );

        if (confirmError) {
          setError(confirmError.message);
          setLoading(false);
          return;
        }
      }

      // Success!
      setSuccess(true);
      setLoading(false);
      
      // Redirect to dashboard after 2 seconds
      setTimeout(() => {
        window.location.href = '/dashboard';
      }, 2000);

    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="success-message">
        <h2>✓ Subscription Successful!</h2>
        <p>Welcome to {selectedPlan.name}</p>
        <p>Redirecting to dashboard...</p>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="checkout-form">
      <h3>Subscribe to {selectedPlan.name}</h3>
      <p className="plan-price">${selectedPlan.price}/{selectedPlan.billing_cycle}</p>

      <div className="form-group">
        <label>Card Details</label>
        <CardElement 
          options={{
            style: {
              base: {
                fontSize: '16px',
                color: '#424770',
                '::placeholder': {
                  color: '#aab7c4',
                },
              },
              invalid: {
                color: '#9e2146',
              },
            },
          }}
        />
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <button 
        type="submit" 
        disabled={!stripe || loading}
        className="btn-pay"
      >
        {loading ? 'Processing...' : `Pay $${selectedPlan.price}`}
      </button>

      <p className="secure-note">
        🔒 Secure payment powered by Stripe
      </p>
    </form>
  );
}

// ==========================================
// STEP 3: Subscription Dashboard
// ==========================================
function SubscriptionDashboard({ jwtToken }) {
  const [subscription, setSubscription] = useState(null);
  const [usage, setUsage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch subscription details
    Promise.all([
      fetch('http://127.0.0.1:8000/api/subscriptions/subscription/', {
        headers: { 'Authorization': `Bearer ${jwtToken}` }
      }).then(res => res.json()),
      fetch('http://127.0.0.1:8000/api/subscriptions/subscription/usage/', {
        headers: { 'Authorization': `Bearer ${jwtToken}` }
      }).then(res => res.json())
    ])
    .then(([subData, usageData]) => {
      setSubscription(subData);
      setUsage(usageData);
      setLoading(false);
    })
    .catch(err => {
      console.error('Error fetching subscription:', err);
      setLoading(false);
    });
  }, [jwtToken]);

  if (loading) return <div>Loading...</div>;

  if (!subscription || subscription.subscription === null) {
    return (
      <div className="no-subscription">
        <h2>No Active Subscription</h2>
        <p>Subscribe to start using our services</p>
        <button onClick={() => window.location.href = '/plans'}>
          View Plans
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <h2>Your Subscription</h2>
      
      <div className="subscription-info">
        <div className="info-card">
          <h3>{subscription.plan.name}</h3>
          <p className="price">${subscription.plan.price}/{subscription.plan.billing_cycle}</p>
          <p className="status">Status: <span className={`badge ${subscription.status}`}>
            {subscription.status}
          </span></p>
        </div>

        <div className="usage-card">
          <h3>Usage This Month</h3>
          <div className="usage-bar">
            <div 
              className="usage-progress" 
              style={{ 
                width: `${usage.usage_percentage}%`,
                backgroundColor: usage.usage_percentage > 80 ? 'red' : 'green'
              }}
            />
          </div>
          <p>
            {usage.requests_used_this_month} / {usage.max_requests_per_month === 999999 ? '∞' : usage.max_requests_per_month} requests used
          </p>
          <p>Remaining: {usage.requests_remaining === 999999 ? '∞' : usage.requests_remaining}</p>
        </div>

        <div className="actions">
          <button className="btn-upgrade">
            Upgrade Plan
          </button>
          <button className="btn-cancel">
            Cancel Subscription
          </button>
        </div>
      </div>
    </div>
  );
}

// ==========================================
// MAIN APP
// ==========================================
function App() {
  const [step, setStep] = useState('plans'); // plans, checkout, dashboard
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [jwtToken, setJwtToken] = useState(localStorage.getItem('jwt_token'));

  const handleSelectPlan = (plan) => {
    setSelectedPlan(plan);
    setStep('checkout');
  };

  // Login form (simplified)
  if (!jwtToken) {
    return (
      <div className="login-form">
        <h2>Login</h2>
        <form onSubmit={async (e) => {
          e.preventDefault();
          const formData = new FormData(e.target);
          const response = await fetch('http://127.0.0.1:8000/api/auth/login/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email: formData.get('email'),
              password: formData.get('password'),
            }),
          });
          const data = await response.json();
          if (data.access) {
            localStorage.setItem('jwt_token', data.access);
            setJwtToken(data.access);
          }
        }}>
          <input name="email" type="email" placeholder="Email" required />
          <input name="password" type="password" placeholder="Password" required />
          <button type="submit">Login</button>
        </form>
      </div>
    );
  }

  return (
    <div className="app">
      {step === 'plans' && (
        <PlanSelection onSelectPlan={handleSelectPlan} />
      )}

      {step === 'checkout' && selectedPlan && (
        <Elements stripe={stripePromise}>
          <CheckoutForm 
            selectedPlan={selectedPlan} 
            jwtToken={jwtToken}
          />
        </Elements>
      )}

      {step === 'dashboard' && (
        <SubscriptionDashboard jwtToken={jwtToken} />
      )}
    </div>
  );
}

export default App;

// ==========================================
// CSS (styles.css)
// ==========================================
/*
.plans-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
}

.plans-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 30px;
  margin-top: 30px;
}

.plan-card {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 30px;
  text-align: center;
  transition: transform 0.3s, box-shadow 0.3s;
}

.plan-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.price {
  font-size: 48px;
  font-weight: bold;
  color: #2c3e50;
  margin: 20px 0;
}

.price span {
  font-size: 18px;
  color: #7f8c8d;
}

.features {
  list-style: none;
  padding: 0;
  text-align: left;
  margin: 30px 0;
}

.features li {
  padding: 10px 0;
  border-bottom: 1px solid #ecf0f1;
}

.btn-subscribe {
  width: 100%;
  padding: 15px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-subscribe:hover {
  background: #2980b9;
}

.checkout-form {
  max-width: 500px;
  margin: 50px auto;
  padding: 40px;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.form-group {
  margin: 30px 0;
}

.form-group label {
  display: block;
  margin-bottom: 10px;
  font-weight: bold;
}

.btn-pay {
  width: 100%;
  padding: 15px;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.3s;
}

.btn-pay:hover {
  background: #229954;
}

.btn-pay:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.error-message {
  background: #e74c3c;
  color: white;
  padding: 15px;
  border-radius: 8px;
  margin: 20px 0;
}

.success-message {
  text-align: center;
  padding: 60px;
}

.success-message h2 {
  color: #27ae60;
  font-size: 32px;
}

.secure-note {
  text-align: center;
  color: #7f8c8d;
  margin-top: 20px;
  font-size: 14px;
}
*/
