from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
import stripe
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import SubscriptionPlan, UserSubscription, PaymentHistory
from .serializers import (
    SubscriptionPlanSerializer, UserSubscriptionSerializer, PaymentHistorySerializer,
    CreateSubscriptionSerializer, UpdateSubscriptionSerializer, CancelSubscriptionSerializer,
    SubscriptionUsageSerializer, SubscriptionStatsSerializer, StripeCustomerSerializer,
    PurchaseReportSerializer
)

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

User = get_user_model()

class SubscriptionPlansView(APIView):
    """View to list all available subscription plans"""
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get all available subscription plans with per-report pricing",
        operation_summary="List Subscription Plans",
        responses={
            200: openapi.Response(
                description="List of subscription plans",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "name": "Basic Plan",
                            "price_per_report": "25.00",
                            "plan_type": "basic",
                            "features": ["Identity Verification", "SSN Trace", "National Criminal Search"],
                            "is_active": True
                        },
                        {
                            "id": 2,
                            "name": "Premium Plan",
                            "price_per_report": "50.00",
                            "plan_type": "premium",
                            "features": ["All Basic features", "Employment Verification", "Education Verification"],
                            "is_active": True
                        }
                    ]
                }
            )
        },
        tags=['Subscriptions']
    )
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_per_report')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)

class UserSubscriptionView(APIView):
    """View to manage user's subscription"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get My Subscription",
        operation_description="Get the authenticated user's current subscription details including plan, status, and usage.",
        operation_id="subscription_get",
        tags=['Subscriptions'],
        responses={
            200: UserSubscriptionSerializer,
            404: "No active subscription found"
        }
    )
    def get(self, request):
        """Get current user's subscription details"""
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            serializer = UserSubscriptionSerializer(subscription)
            return Response(serializer.data)
        except UserSubscription.DoesNotExist:
            return Response({
                'subscription': None,
                'message': 'No active subscription found'
            })
    
    @swagger_auto_schema(
        operation_summary="Create New Subscription",
        operation_description="Subscribe to a plan using Stripe. Creates Stripe customer and subscription.",
        operation_id="subscription_create",
        tags=['Subscriptions'],
        request_body=CreateSubscriptionSerializer,
        responses={
            201: UserSubscriptionSerializer,
            400: "Bad request - Invalid data or user already has subscription",
            404: "Plan not found"
        }
    )
    def post(self, request):
        """Create a new subscription for the user - Per-Report Payment Model"""
        serializer = CreateSubscriptionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                plan_id = serializer.validated_data['plan_id']
                
                plan = SubscriptionPlan.objects.get(id=plan_id)
                
                # Get or create user subscription (Per-Report Model - No Stripe subscription needed)
                subscription, created = UserSubscription.objects.get_or_create(
                    user=request.user,
                    defaults={'plan': plan}
                )
                
                if not created:
                    # Update existing subscription with new plan
                    subscription.plan = plan
                    subscription.save()
                    message = 'Subscription plan updated successfully'
                else:
                    message = 'Subscription created successfully'
                
                response_data = {
                    'message': message,
                    'subscription': UserSubscriptionSerializer(subscription).data
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
                
            except SubscriptionPlan.DoesNotExist:
                return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Update Subscription Plan",
        operation_description="Change subscription plan. Updates both Stripe subscription and local records.",
        operation_id="subscription_update",
        tags=['Subscriptions'],
        request_body=UpdateSubscriptionSerializer,
        responses={
            200: UserSubscriptionSerializer,
            400: "Bad request",
            404: "Subscription or plan not found"
        }
    )
    def patch(self, request):
        """Update user's subscription plan"""
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            serializer = UpdateSubscriptionSerializer(data=request.data)
            
            if serializer.is_valid():
                new_plan_id = serializer.validated_data['plan_id']
                prorate = serializer.validated_data.get('prorate', True)
                
                new_plan = SubscriptionPlan.objects.get(id=new_plan_id)
                
                # Update Stripe subscription
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    items=[{
                        'id': stripe.Subscription.retrieve(subscription.stripe_subscription_id).items.data[0].id,
                        'price': new_plan.stripe_price_id,
                    }],
                    proration_behavior='create_prorations' if prorate else 'none'
                )
                
                # Update local subscription
                subscription.plan = new_plan
                subscription.save()
                
                return Response({
                    'message': 'Subscription updated successfully',
                    'subscription': UserSubscriptionSerializer(subscription).data
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except UserSubscription.DoesNotExist:
            return Response({'error': 'No subscription found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(
        operation_summary="Cancel Subscription",
        operation_description="Cancel the user's subscription. Can cancel immediately or at the end of billing period.",
        operation_id="subscription_cancel",
        tags=['Subscriptions'],
        request_body=CancelSubscriptionSerializer,
        responses={
            200: UserSubscriptionSerializer,
            400: "Bad request",
            404: "No subscription found"
        }
    )
    def delete(self, request):
        """Cancel user's subscription"""
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            serializer = CancelSubscriptionSerializer(data=request.data)
            
            if serializer.is_valid():
                cancel_at_period_end = serializer.validated_data.get('cancel_at_period_end', True)
                
                # Cancel Stripe subscription
                if cancel_at_period_end:
                    stripe.Subscription.modify(
                        subscription.stripe_subscription_id,
                        cancel_at_period_end=True
                    )
                    subscription.status = 'active'  # Keep active until period ends
                else:
                    stripe.Subscription.cancel(subscription.stripe_subscription_id)
                    subscription.status = 'canceled'
                    subscription.end_date = timezone.now()
                
                subscription.save()
                
                return Response({
                    'message': 'Subscription canceled successfully',
                    'subscription': UserSubscriptionSerializer(subscription).data
                })
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except UserSubscription.DoesNotExist:
            return Response({'error': 'No subscription found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def get_or_create_stripe_customer(self, user):
        """Get or create a Stripe customer for the user"""
        try:
            # Try to find existing customer
            subscription = UserSubscription.objects.filter(user=user).first()
            if subscription and subscription.stripe_customer_id:
                return stripe.Customer.retrieve(subscription.stripe_customer_id)
        except:
            pass
        
        # Create new customer
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name} {user.last_name}".strip() or user.username,
            metadata={'user_id': user.id}
        )
        
        return customer

class SubscriptionUsageView(APIView):
    """View to get user's subscription usage information"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get Subscription Usage",
        operation_description="Get current subscription usage statistics including requests used and remaining.",
        operation_id="subscription_usage",
        tags=['Subscriptions'],
        responses={
            200: SubscriptionUsageSerializer
        }
    )
    def get(self, request):
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            
            usage_data = {
                'current_plan': subscription.plan,
                'total_reports_purchased': subscription.total_reports_purchased,
                'total_reports_used': subscription.total_reports_used,
                'available_reports': subscription.available_reports,
                'free_trial_used': subscription.free_trial_used,
                'can_use_free_trial': subscription.can_use_free_trial,
                'can_make_request': subscription.can_make_request
            }
            
            serializer = SubscriptionUsageSerializer(usage_data)
            return Response(serializer.data)
            
        except UserSubscription.DoesNotExist:
            return Response({
                'current_plan': None,
                'total_reports_purchased': 0,
                'total_reports_used': 0,
                'available_reports': 0,
                'free_trial_used': False,
                'can_use_free_trial': True,
                'can_make_request': True  # New users can use free trial
            })

class PaymentHistoryView(APIView):
    """View to get user's payment history"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Get Payment History",
        operation_description="Get list of all past payments and invoices from Stripe.",
        operation_id="subscription_payment_history",
        tags=['Payments'],
        responses={
            200: openapi.Response(
                description="List of payments",
                examples={
                    "application/json": {
                        "payments": []
                    }
                }
            )
        }
    )
    def get(self, request):
        payments = PaymentHistory.objects.filter(user=request.user).order_by('-created_at')
        serializer = PaymentHistorySerializer(payments, many=True)
        return Response(serializer.data)

class StripeWebhookView(APIView):
    """View to handle Stripe webhooks"""
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_summary="Stripe Webhook Handler",
        operation_description="Webhook endpoint for Stripe events. Handles subscription updates, payments, and cancellations. This endpoint is called by Stripe, not by users.",
        operation_id="stripe_webhook",
        tags=['Payments'],
        responses={
            200: "Webhook processed successfully",
            400: "Invalid payload or signature"
        }
    )
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_ENDPOINT_SECRET
            )
        except ValueError:
            return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            self.handle_checkout_session_completed(event['data']['object'])
        elif event['type'] == 'payment_intent.succeeded':
            self.handle_payment_succeeded(event['data']['object'])
        elif event['type'] == 'payment_intent.payment_failed':
            self.handle_payment_failed(event['data']['object'])
        elif event['type'] == 'customer.subscription.updated':
            self.handle_subscription_updated(event['data']['object'])
        elif event['type'] == 'customer.subscription.deleted':
            self.handle_subscription_deleted(event['data']['object'])
        elif event['type'] == 'invoice.payment_succeeded':
            self.handle_invoice_payment_succeeded(event['data']['object'])
        
        return Response({'status': 'success'})
    
    def handle_checkout_session_completed(self, session):
        """Handle completed checkout session"""
        try:
            # Get user from metadata
            user_id = session['metadata'].get('user_id')
            plan_id = session['metadata'].get('plan_id')
            
            if not user_id or not plan_id:
                return
            
            user = User.objects.get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            stripe_subscription_id = session.get('subscription')
            stripe_customer_id = session.get('customer')
            
            # Retrieve full subscription details from Stripe
            stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            # Create or update subscription
            user_subscription, created = UserSubscription.objects.update_or_create(
                user=user,
                defaults={
                    'plan': plan,
                    'stripe_subscription_id': stripe_subscription_id,
                    'stripe_customer_id': stripe_customer_id,
                    'status': 'active' if stripe_subscription.status == 'active' else stripe_subscription.status,
                    'start_date': timezone.now(),
                    'end_date': timezone.datetime.fromtimestamp(
                        stripe_subscription.current_period_end,
                        tz=timezone.get_current_timezone()
                    ),
                    'trial_end': timezone.datetime.fromtimestamp(
                        stripe_subscription.trial_end,
                        tz=timezone.get_current_timezone()
                    ) if stripe_subscription.trial_end else None,
                }
            )
            
            # Create payment record
            PaymentHistory.objects.create(
                user=user,
                subscription=user_subscription,
                amount=plan.price,
                currency='USD',
                status='succeeded',
                stripe_payment_intent_id=session.get('payment_intent'),
                description=f"Subscription to {plan.name} via Checkout"
            )
            
        except (User.DoesNotExist, SubscriptionPlan.DoesNotExist):
            pass
        except Exception as e:
            print(f"Error handling checkout session: {str(e)}")
    
    def handle_payment_succeeded(self, payment_intent):
        """Handle successful payment"""
        try:
            subscription = UserSubscription.objects.get(
                stripe_customer_id=payment_intent['customer']
            )
            
            PaymentHistory.objects.create(
                user=subscription.user,
                subscription=subscription,
                amount=payment_intent['amount'] / 100,  # Convert from cents
                currency=payment_intent['currency'].upper(),
                status='succeeded',
                stripe_payment_intent_id=payment_intent['id'],
                description=f"Payment for {subscription.plan.name}"
            )
            
        except UserSubscription.DoesNotExist:
            pass
    
    def handle_payment_failed(self, payment_intent):
        """Handle failed payment"""
        try:
            subscription = UserSubscription.objects.get(
                stripe_customer_id=payment_intent['customer']
            )
            
            PaymentHistory.objects.create(
                user=subscription.user,
                subscription=subscription,
                amount=payment_intent['amount'] / 100,
                currency=payment_intent['currency'].upper(),
                status='failed',
                stripe_payment_intent_id=payment_intent['id'],
                failure_reason=payment_intent.get('last_payment_error', {}).get('message', 'Payment failed'),
                description=f"Failed payment for {subscription.plan.name}"
            )
            
        except UserSubscription.DoesNotExist:
            pass
    
    def handle_subscription_updated(self, subscription_obj):
        """Handle subscription updates from Stripe"""
        try:
            user_subscription = UserSubscription.objects.get(
                stripe_subscription_id=subscription_obj['id']
            )
            
            user_subscription.status = subscription_obj['status']
            user_subscription.save()
            
        except UserSubscription.DoesNotExist:
            pass
    
    def handle_subscription_deleted(self, subscription_obj):
        """Handle subscription cancellation from Stripe"""
        try:
            user_subscription = UserSubscription.objects.get(
                stripe_subscription_id=subscription_obj['id']
            )
            
            user_subscription.status = 'canceled'
            user_subscription.end_date = timezone.now()
            user_subscription.save()
            
        except UserSubscription.DoesNotExist:
            pass
    
    def handle_invoice_payment_succeeded(self, invoice):
        """Handle successful invoice payment"""
        try:
            subscription = UserSubscription.objects.get(
                stripe_subscription_id=invoice['subscription']
            )
            
            # Update subscription status to active
            subscription.status = 'active'
            subscription.save()
            
        except UserSubscription.DoesNotExist:
            pass

class AdminSubscriptionStatsView(APIView):
    """Admin view for subscription statistics"""
    permission_classes = [permissions.IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="Get Subscription Statistics (Admin)",
        operation_description="Get system-wide subscription statistics including revenue, subscriber counts, and popular plans. Admin only.",
        operation_id="subscription_admin_stats",
        tags=['Admin - Subscriptions'],
        responses={
            200: SubscriptionStatsSerializer,
            403: "Admin access required"
        }
    )
    def get(self, request):
        # Calculate statistics
        total_subscribers = UserSubscription.objects.count()
        active_subscribers = UserSubscription.objects.filter(plan__isnull=False).count()
        
        # Calculate revenue
        total_revenue = PaymentHistory.objects.filter(
            status='succeeded'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Monthly revenue (current month)
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = PaymentHistory.objects.filter(
            status='succeeded',
            created_at__gte=current_month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Most popular plan
        popular_plan_data = UserSubscription.objects.filter(
            plan__isnull=False
        ).values('plan__name').annotate(
            count=Count('plan')
        ).order_by('-count').first()
        
        most_popular_plan = None
        if popular_plan_data:
            most_popular_plan = SubscriptionPlan.objects.get(name=popular_plan_data['plan__name'])
        
        # Recent payments
        recent_payments = PaymentHistory.objects.all().order_by('-created_at')[:10]
        
        stats_data = {
            'total_subscribers': total_subscribers,
            'active_subscribers': active_subscribers,
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'most_popular_plan': most_popular_plan,
            'recent_payments': recent_payments
        }
        
        serializer = SubscriptionStatsSerializer(stats_data)
        return Response(serializer.data)


class CreateCheckoutSessionView(APIView):
    """Create Stripe Checkout Session for subscription purchase"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Create Stripe Checkout Session",
        operation_description="Create a Stripe Checkout Session for subscribing to a plan. Returns checkout URL to redirect user to Stripe payment page.",
        operation_id="subscription_create_checkout",
        tags=['Payments'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['plan_id'],
            properties={
                'plan_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Subscription plan ID'),
                'trial_period_days': openapi.Schema(type=openapi.TYPE_INTEGER, description='Trial period in days', default=0)
            }
        ),
        responses={
            200: openapi.Response(
                description="Checkout session created",
                examples={
                    "application/json": {
                        "checkout_url": "https://checkout.stripe.com/...",
                        "session_id": "cs_test_..."
                    }
                }
            ),
            400: "Bad request",
            404: "Plan not found"
        }
    )
    def post(self, request):
        """Create a Checkout Session and return the URL"""
        try:
            plan_id = request.data.get('plan_id')
            trial_period_days = request.data.get('trial_period_days', 0)
            
            # Validate plan
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                return Response(
                    {'error': 'Invalid subscription plan'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get or create user subscription
            subscription, created = UserSubscription.objects.get_or_create(
                user=request.user,
                defaults={'plan': plan}
            )
            
            if not created and subscription.plan:
                return Response(
                    {'error': 'User already has a subscription. Use purchase-report endpoint to buy more reports.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create Stripe customer
            customer = self.get_or_create_stripe_customer(request.user)
            
            # Determine the success and cancel URLs - Use production backend URL
            backend_url = 'https://h2o427-backend-u9bx.onrender.com'
            success_url = f"{backend_url}/api/subscriptions/ui/success/?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{backend_url}/api/subscriptions/ui/cancel/"
            
            # Create Checkout Session
            checkout_session_params = {
                'customer': customer.id,
                'payment_method_types': ['card'],
                'line_items': [{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'metadata': {
                    'user_id': request.user.id,
                    'plan_id': plan.id,
                }
            }
            
            # Add trial if specified
            if trial_period_days > 0:
                checkout_session_params['subscription_data'] = {
                    'trial_period_days': trial_period_days
                }
            
            # Create the session
            checkout_session = stripe.checkout.Session.create(**checkout_session_params)
            
            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id,
                'plan': SubscriptionPlanSerializer(plan).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def get_or_create_stripe_customer(self, user):
        """Get or create a Stripe customer for the user"""
        try:
            # Try to find existing customer
            subscription = UserSubscription.objects.filter(user=user).first()
            if subscription and subscription.stripe_customer_id:
                return stripe.Customer.retrieve(subscription.stripe_customer_id)
        except:
            pass
        
        # Create new customer
        customer = stripe.Customer.create(
            email=user.email,
            name=getattr(user, 'full_name', None) or f"{user.first_name} {user.last_name}".strip() or user.username,
            metadata={'user_id': user.id}
        )
        
        return customer


class VerifyCheckoutSessionView(APIView):
    """Verify Checkout Session and create subscription"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Verify Stripe Checkout Session",
        operation_description="Verify that a Stripe Checkout Session was completed successfully after user returns from Stripe payment page.",
        operation_id="subscription_verify_checkout",
        tags=['Payments'],
        manual_parameters=[
            openapi.Parameter('session_id', openapi.IN_QUERY, description="Stripe checkout session ID", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: openapi.Response(
                description="Checkout session verified",
                examples={
                    "application/json": {
                        "success": True,
                        "message": "Subscription activated successfully",
                        "subscription": {}
                    }
                }
            ),
            400: "Bad request or payment not completed",
            404: "Session not found"
        }
    )
    def get(self, request):
        """Verify the checkout session and create/update subscription"""
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'Session ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Retrieve the checkout session from Stripe
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            # Check if payment was successful
            if checkout_session.payment_status != 'paid':
                return Response({
                    'status': 'pending',
                    'message': 'Payment is still being processed'
                })
            
            # Get the subscription ID from Stripe
            stripe_subscription_id = checkout_session.subscription
            stripe_customer_id = checkout_session.customer
            
            # Retrieve plan from metadata
            plan_id = checkout_session.metadata.get('plan_id')
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Retrieve the subscription from Stripe to get details
            stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
            
            # Create or update local subscription
            user_subscription, created = UserSubscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'stripe_subscription_id': stripe_subscription_id,
                    'stripe_customer_id': stripe_customer_id,
                    'status': 'active' if stripe_subscription.status == 'active' else stripe_subscription.status,
                    'start_date': timezone.now(),
                    'end_date': timezone.datetime.fromtimestamp(
                        stripe_subscription.current_period_end, 
                        tz=timezone.get_current_timezone()
                    ),
                    'trial_end': timezone.datetime.fromtimestamp(
                        stripe_subscription.trial_end, 
                        tz=timezone.get_current_timezone()
                    ) if stripe_subscription.trial_end else None,
                }
            )
            
            # Create payment history record
            PaymentHistory.objects.create(
                user=request.user,
                subscription=user_subscription,
                amount=plan.price,
                currency='USD',
                status='succeeded',
                stripe_payment_intent_id=checkout_session.payment_intent,
                description=f"Subscription to {plan.name}"
            )
            
            return Response({
                'status': 'success',
                'message': 'Subscription created successfully',
                'subscription': UserSubscriptionSerializer(user_subscription).data
            })
            
        except Exception as e:
            # Handle Stripe errors and other exceptions
            error_message = str(e)
            if 'No such checkout.session' in error_message or 'session_id' in error_message.lower():
                return Response(
                    {'error': 'Invalid or expired checkout session ID'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'error': error_message}, 
                status=status.HTTP_400_BAD_REQUEST
            )


# ==================== Per-Report Purchase Views ====================

class PurchaseReportView(APIView):
    """Purchase background check reports"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Purchase Reports",
        operation_description="Create Stripe Checkout Session for purchasing background check reports. Redirects to Stripe's official checkout page.",
        operation_id="subscription_purchase_reports",
        tags=['Subscriptions'],
        request_body=PurchaseReportSerializer,
        responses={
            200: openapi.Response(
                description="Checkout session created - redirect user to checkout_url",
                examples={
                    "application/json": {
                        "checkout_url": "https://checkout.stripe.com/c/pay/xxx",
                        "session_id": "cs_test_xxx",
                        "amount": 25.00,
                        "quantity": 1,
                        "plan": "Basic Plan"
                    }
                }
            ),
            400: "Bad request",
            404: "Plan not found"
        }
    )
    def post(self, request):
        """Create Stripe Checkout Session for report purchase"""
        serializer = PurchaseReportSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            plan_id = serializer.validated_data['plan_id']
            quantity = serializer.validated_data.get('quantity', 1)
            
            # Get plan
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            
            # Calculate amount
            amount = float(plan.price_per_report) * quantity
            
            # Get or create user subscription
            subscription, created = UserSubscription.objects.get_or_create(
                user=request.user,
                defaults={'plan': plan}
            )
            
            # Update plan if changed
            if subscription.plan != plan:
                subscription.plan = plan
                subscription.save()
            
            # Get or create Stripe customer
            if not subscription.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=request.user.email,
                    name=f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                    metadata={'user_id': request.user.id}
                )
                subscription.stripe_customer_id = customer.id
                subscription.save()
            
            # Create Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                customer=subscription.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': int(float(plan.price_per_report) * 100),  # Convert to cents
                        'product_data': {
                            'name': f"{plan.name} - Background Check Report",
                            'description': plan.description,
                        },
                    },
                    'quantity': quantity,
                }],
                mode='payment',
                success_url=request.build_absolute_uri('/api/subscriptions/confirm-payment/?session_id={CHECKOUT_SESSION_ID}'),
                cancel_url=request.build_absolute_uri('/api/subscriptions/purchase-cancelled/'),
                metadata={
                    'user_id': request.user.id,
                    'plan_id': plan.id,
                    'quantity': quantity,
                    'subscription_id': subscription.id
                }
            )
            
            return Response({
                'checkout_url': checkout_session.url,
                'session_id': checkout_session.id,
                'amount': amount,
                'quantity': quantity,
                'plan': plan.name,
                'plan_price': float(plan.price_per_report)
            }, status=status.HTTP_200_OK)
            
        except SubscriptionPlan.DoesNotExist:
            return Response(
                {'error': 'Plan not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class ConfirmPaymentView(APIView):
    """Confirm payment from Stripe Checkout Session and add reports to user account"""
    permission_classes = [permissions.AllowAny]  # Changed to AllowAny for redirect callback
    
    @swagger_auto_schema(
        operation_summary="Confirm Payment",
        operation_description="Confirm payment was successful from Stripe Checkout and add purchased reports to user account.",
        operation_id="subscription_confirm_payment",
        tags=['Subscriptions'],
        manual_parameters=[
            openapi.Parameter('session_id', openapi.IN_QUERY, description="Stripe Checkout Session ID", type=openapi.TYPE_STRING, required=True)
        ],
        responses={
            200: UserSubscriptionSerializer,
            400: "Bad request",
            404: "Payment not found"
        }
    )
    def get(self, request):
        """Verify Stripe Checkout Session and add reports"""
        session_id = request.query_params.get('session_id')
        
        if not session_id:
            return Response(
                {'error': 'Checkout session ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Retrieve checkout session from Stripe
            checkout_session = stripe.checkout.Session.retrieve(session_id)
            
            # Check if payment was successful
            if checkout_session.payment_status != 'paid':
                return Response(
                    {'error': 'Payment not completed', 'status': checkout_session.payment_status}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get metadata
            user_id = int(checkout_session.metadata.get('user_id'))
            plan_id = int(checkout_session.metadata.get('plan_id'))
            quantity = int(checkout_session.metadata.get('quantity', 1))
            subscription_id = int(checkout_session.metadata.get('subscription_id'))
            
            # Get user and subscription
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            subscription = UserSubscription.objects.get(id=subscription_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Add reports to subscription
            subscription.total_reports_purchased += quantity
            subscription.save()
            
            # Calculate amount
            amount = float(plan.price_per_report) * quantity
            
            # Create payment history
            PaymentHistory.objects.create(
                user=user,
                subscription=subscription,
                plan=plan,
                amount=amount,
                reports_purchased=quantity,
                currency='USD',
                status='succeeded',
                stripe_payment_intent_id=checkout_session.payment_intent,
                description=f"Purchase of {quantity} {plan.name} report{'s' if quantity > 1 else ''}"
            )
            
            return Response({
                'message': 'Payment confirmed successfully',
                'reports_added': quantity,
                'available_reports': subscription.total_reports_purchased - subscription.total_reports_used,
                'subscription': UserSubscriptionSerializer(subscription).data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Handle all errors including Stripe errors
            error_message = str(e)
            if 'checkout.session' in error_message.lower() or 'session_id' in error_message.lower():
                return Response(
                    {'error': 'Invalid or expired checkout session'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            return Response(
                {'error': f'Error processing payment: {error_message}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class PurchaseCancelledView(APIView):
    """Handle cancelled purchase"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        """User cancelled the purchase"""
        return Response({
            'message': 'Purchase cancelled',
            'status': 'cancelled'
        }, status=status.HTTP_200_OK)


# ==================== TEST ENDPOINT (For API Testing Without Stripe) ====================

class TestPurchaseReportsView(APIView):
    """TEST ONLY: Direct purchase without Stripe payment - Use for API testing"""
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="Test Purchase Reports (No Stripe)",
        operation_description="FOR TESTING ONLY: Purchase reports directly without Stripe payment. Use this endpoint when testing API flow in Postman.",
        operation_id="test_purchase_reports",
        tags=['Subscriptions - Testing'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['quantity'],
            properties={
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of reports to purchase', minimum=1)
            }
        ),
        responses={
            200: "Reports added successfully",
            400: "Bad request",
            404: "Subscription not found"
        }
    )
    def post(self, request):
        """Add reports to account without payment - FOR TESTING ONLY"""
        quantity = request.data.get('quantity')
        
        if not quantity or quantity < 1:
            return Response(
                {'error': 'Valid quantity is required (minimum 1)'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get user subscription
            subscription = UserSubscription.objects.get(user=request.user)
            plan = subscription.plan
            
            if not plan:
                return Response(
                    {'error': 'Please select a plan first'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate amount (for reference only, no payment)
            amount = float(plan.price_per_report) * quantity
            
            # Add reports directly
            subscription.total_reports_purchased += quantity
            subscription.save()
            
            # Create payment history record (marked as test)
            PaymentHistory.objects.create(
                user=request.user,
                subscription=subscription,
                plan=plan,
                amount=amount,
                reports_purchased=quantity,
                currency='USD',
                status='succeeded',
                stripe_payment_intent_id=f'test_{timezone.now().timestamp()}',
                description=f"TEST: Purchase of {quantity} {plan.name} report{'s' if quantity > 1 else ''}"
            )
            
            return Response({
                'message': f'TEST: Successfully added {quantity} report{"s" if quantity > 1 else ""}',
                'note': 'This is a test purchase - no actual payment was processed',
                'subscription': UserSubscriptionSerializer(subscription).data,
                'amount_reference': f'${amount:.2f} (not charged)'
            }, status=status.HTTP_200_OK)
            
        except UserSubscription.DoesNotExist:
            return Response(
                {'error': 'No subscription found. Please select a plan first.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


# ==================== Template-Based Views (MVT Pattern) ====================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def plans_list_view(request):
    """Display all subscription plans in a beautiful UI - Per-Report Pricing"""
    if not request.user.is_authenticated:
        return redirect('/admin/login/')
    
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price_per_report')
    
    # Convert plans to dict format with features list
    plans_data = []
    for plan in plans:
        # Build feature list from plan's boolean fields
        feature_list = []
        
        # Add features based on boolean fields
        if plan.identity_verification:
            feature_list.append({'name': 'Identity Verification'})
        if plan.ssn_trace:
            feature_list.append({'name': 'SSN Trace'})
        if plan.national_criminal_search:
            feature_list.append({'name': 'National Criminal Search'})
        if plan.sex_offender_registry:
            feature_list.append({'name': 'Sex Offender Registry'})
        if plan.employment_verification:
            feature_list.append({'name': 'Employment History Verification'})
        if plan.education_verification:
            feature_list.append({'name': 'Education Verification'})
        if plan.unlimited_county_search:
            feature_list.append({'name': 'Unlimited County Criminal Search'})
        if plan.priority_support:
            feature_list.append({'name': 'Priority Support'})
        else:
            feature_list.append({'name': 'Standard Support'})
        
        plans_data.append({
            'id': plan.id,
            'name': plan.name,
            'price': plan.price_per_report,
            'billing_interval': 'per report',
            'description': plan.description,
            'features': feature_list,
            'stripe_price_id': plan.stripe_price_id,
        })
    
    return render(request, 'subscriptions/plans.html', {
        'plans': plans_data,
        'user': request.user
    })


@login_required
def subscribe_plan_view(request):
    """Handle subscription creation via Stripe Checkout"""
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Get or create user subscription
            subscription, created = UserSubscription.objects.get_or_create(
                user=request.user,
                defaults={'plan': plan}
            )
            
            if not created and subscription.plan:
                messages.warning(request, 'You already have a subscription! You can purchase more reports.')
                return redirect('subscriptions:subscription_dashboard')
            
            # Create or get Stripe customer
            if not request.user.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=request.user.email,
                    name=request.user.get_full_name() or request.user.email,
                )
                request.user.stripe_customer_id = customer.id
                request.user.save()
            
            # Create Stripe Checkout Session
            checkout_session = stripe.checkout.Session.create(
                customer=request.user.stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=request.build_absolute_uri('/api/subscriptions/ui/success/') + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri('/api/subscriptions/ui/cancel/'),
                metadata={
                    'user_id': request.user.id,
                    'plan_id': plan.id,
                }
            )
            
            # Redirect to Stripe Checkout
            return redirect(checkout_session.url)
            
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, 'Selected plan does not exist!')
            return redirect('subscriptions:plans_list')
        except Exception as e:
            messages.error(request, f'Error creating checkout session: {str(e)}')
            return redirect('subscriptions:plans_list')
    
    return redirect('subscriptions:plans_list')


def subscription_success_view(request):
    """Handle successful payment and display success page"""
    session_id = request.GET.get('session_id')
    
    if not session_id:
        return render(request, 'subscriptions/success.html', {
            'subscription': None
        })
    
    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            user_id = session.metadata.get('user_id')
            plan_id = session.metadata.get('plan_id')
            
            user = User.objects.get(id=user_id)
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Check if subscription already exists
            subscription, created = UserSubscription.objects.get_or_create(
                user=user,
                stripe_subscription_id=session.subscription,
                defaults={
                    'plan': plan,
                    'status': 'active',
                    'start_date': timezone.now(),
                    'end_date': timezone.now() + timedelta(days=30 if plan.billing_cycle == 'monthly' else 365),
                    'stripe_customer_id': session.customer,
                }
            )
            
            if created:
                # Create payment history
                PaymentHistory.objects.create(
                    user=user,
                    subscription=subscription,
                    amount=plan.price,
                    currency='usd',
                    status='succeeded',
                    stripe_payment_intent_id=session.payment_intent,
                )
            
            return render(request, 'subscriptions/success.html', {
                'subscription': subscription
            })
    except Exception as e:
        messages.error(request, f'Error verifying payment: {str(e)}')
    
    return render(request, 'subscriptions/success.html', {
        'subscription': None
    })


def subscription_cancel_view(request):
    """Handle cancelled payment"""
    return render(request, 'subscriptions/cancel.html')


@login_required
def subscription_dashboard_view(request):
    """Display user's subscription dashboard - Per-Report Pricing"""
    try:
        subscription = UserSubscription.objects.select_related('plan').get(
            user=request.user
        )
        
        # Calculate usage percentage based on purchased reports
        usage_percentage = 0
        if subscription.total_reports_purchased > 0:
            usage_percentage = (subscription.total_reports_used / subscription.total_reports_purchased) * 100
        
        return render(request, 'subscriptions/dashboard.html', {
            'subscription': subscription,
            'usage_percentage': min(usage_percentage, 100),
            'available_reports': subscription.available_reports,
            'free_trial_available': subscription.can_use_free_trial
        })
    except UserSubscription.DoesNotExist:
        return render(request, 'subscriptions/dashboard.html', {
            'subscription': None,
            'usage_percentage': 0,
            'available_reports': 0,
            'free_trial_available': True  # New users get free trial
        })
