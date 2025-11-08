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

from .models import SubscriptionPlan, UserSubscription, PaymentHistory, SubscriptionFeature
from .serializers import (
    SubscriptionPlanSerializer, UserSubscriptionSerializer, PaymentHistorySerializer,
    CreateSubscriptionSerializer, UpdateSubscriptionSerializer, CancelSubscriptionSerializer,
    SubscriptionUsageSerializer, SubscriptionStatsSerializer, StripeCustomerSerializer
)

# Configure Stripe
stripe.api_key = settings.STRIPE_TEST_SECRET_KEY

User = get_user_model()

class SubscriptionPlansView(APIView):
    """View to list all available subscription plans"""
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Get all available subscription plans",
        operation_summary="List Subscription Plans",
        responses={
            200: openapi.Response(
                description="List of subscription plans",
                examples={
                    "application/json": [
                        {
                            "id": 1,
                            "name": "Basic Plan",
                            "price": "9.99",
                            "billing_cycle": "monthly",
                            "max_requests_per_month": 10,
                            "features": ["Feature 1", "Feature 2"],
                            "is_active": True
                        },
                        {
                            "id": 2,
                            "name": "Premium Plan",
                            "price": "29.99",
                            "billing_cycle": "monthly",
                            "max_requests_per_month": 50,
                            "features": ["Feature 1", "Feature 2", "Feature 3"],
                            "is_active": True
                        }
                    ]
                }
            )
        },
        tags=['Subscriptions']
    )
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
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
        """Create a new subscription for the user"""
        serializer = CreateSubscriptionSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                plan_id = serializer.validated_data['plan_id']
                payment_method_id = serializer.validated_data.get('payment_method_id')
                trial_period_days = serializer.validated_data.get('trial_period_days', 0)
                
                plan = SubscriptionPlan.objects.get(id=plan_id)
                
                # Check if user already has an active subscription
                existing_subscription = UserSubscription.objects.filter(
                    user=request.user, 
                    status='active'
                ).first()
                
                if existing_subscription:
                    return Response(
                        {'error': 'User already has an active subscription'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Create or get Stripe customer
                customer = self.get_or_create_stripe_customer(request.user)
                
                # Create Stripe subscription
                subscription_data = {
                    'customer': customer.id,
                    'items': [{'price': plan.stripe_price_id}],
                    'payment_behavior': 'default_incomplete',
                    'payment_settings': {'save_default_payment_method': 'on_subscription'},
                    'expand': ['latest_invoice.payment_intent'],
                }
                
                if trial_period_days > 0:
                    subscription_data['trial_period_days'] = trial_period_days
                
                if payment_method_id:
                    subscription_data['default_payment_method'] = payment_method_id
                
                stripe_subscription = stripe.Subscription.create(**subscription_data)
                
                # Create or update local subscription
                user_subscription, created = UserSubscription.objects.get_or_create(
                    user=request.user,
                    defaults={
                        'plan': plan,
                        'stripe_subscription_id': stripe_subscription.id,
                        'stripe_customer_id': customer.id,
                        'status': 'active' if trial_period_days > 0 else 'incomplete',
                        'start_date': timezone.now(),
                        'trial_end': timezone.now() + timedelta(days=trial_period_days) if trial_period_days > 0 else None
                    }
                )
                
                if not created:
                    user_subscription.plan = plan
                    user_subscription.stripe_subscription_id = stripe_subscription.id
                    user_subscription.stripe_customer_id = customer.id
                    user_subscription.status = 'active' if trial_period_days > 0 else 'incomplete'
                    user_subscription.start_date = timezone.now()
                    user_subscription.trial_end = timezone.now() + timedelta(days=trial_period_days) if trial_period_days > 0 else None
                    user_subscription.save()
                
                response_data = {
                    'subscription': UserSubscriptionSerializer(user_subscription).data,
                    'client_secret': stripe_subscription.latest_invoice.payment_intent.client_secret if hasattr(stripe_subscription.latest_invoice, 'payment_intent') else None,
                    'stripe_subscription_id': stripe_subscription.id
                }
                
                return Response(response_data, status=status.HTTP_201_CREATED)
                
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
                'requests_used_this_month': subscription.requests_used_this_month,
                'requests_remaining': subscription.remaining_requests,
                'max_requests_per_month': subscription.plan.max_requests_per_month if subscription.plan else 0,
                'can_make_request': subscription.can_make_request,
                'subscription_status': subscription.status,
                'next_billing_date': subscription.end_date
            }
            
            serializer = SubscriptionUsageSerializer(usage_data)
            return Response(serializer.data)
            
        except UserSubscription.DoesNotExist:
            return Response({
                'current_plan': None,
                'requests_used_this_month': 0,
                'requests_remaining': 0,
                'max_requests_per_month': 0,
                'can_make_request': False,
                'subscription_status': 'inactive',
                'next_billing_date': None
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
                payload, sig_header, settings.STRIPE_TEST_ENDPOINT_SECRET
            )
        except ValueError:
            return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
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
        active_subscribers = UserSubscription.objects.filter(status='active').count()
        
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
            status='active'
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
            
            # Check if user already has an active subscription
            existing_subscription = UserSubscription.objects.filter(
                user=request.user, 
                status='active'
            ).first()
            
            if existing_subscription:
                return Response(
                    {'error': 'User already has an active subscription'}, 
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
            
        except stripe.error.InvalidRequestError as e:
            return Response(
                {'error': 'Invalid session ID'}, 
                status=status.HTTP_400_BAD_REQUEST
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
    """Display all subscription plans in a beautiful UI"""
    if not request.user.is_authenticated:
        return redirect('/admin/login/')
    
    plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price').prefetch_related('features')
    
    # Convert plans to dict format with features list
    plans_data = []
    for plan in plans:
        # Build feature list from plan's boolean fields and PlanFeature relationships
        feature_list = []
        
        # Add features based on boolean fields
        if plan.basic_identity_verification:
            feature_list.append({'name': 'Basic identity verification'})
        if plan.criminal_records_search:
            feature_list.append({'name': 'County criminal records search'})
        if plan.federal_records_search:
            feature_list.append({'name': 'Federal, state & county criminal records'})
        if plan.employment_verification:
            feature_list.append({'name': 'Employment history verification'})
        if plan.education_verification:
            feature_list.append({'name': 'Education verification'})
        if plan.api_access:
            feature_list.append({'name': 'API Access'})
        if plan.priority_support:
            feature_list.append({'name': 'Priority Support'})
        else:
            feature_list.append({'name': 'Standard support'})
        if plan.advanced_reports:
            feature_list.append({'name': '30-day report access'})
        
        # Add features from PlanFeature relationships if any
        for pf in plan.features.all():
            if pf.is_included:
                feature_list.append({'name': pf.feature.name})
        
        plans_data.append({
            'id': plan.id,
            'name': plan.name,
            'price': plan.price,
            'billing_interval': plan.billing_cycle,
            'description': plan.description,
            'max_requests_per_month': plan.max_requests_per_month,
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
            
            # Check if user already has an active subscription
            existing_subscription = UserSubscription.objects.filter(
                user=request.user,
                status='active'
            ).first()
            
            if existing_subscription:
                messages.warning(request, 'You already have an active subscription!')
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
    """Display user's subscription dashboard"""
    try:
        subscription = UserSubscription.objects.select_related('plan').prefetch_related('plan__features').get(
            user=request.user,
            status='active'
        )
        
        # Calculate usage percentage
        usage_percentage = 0
        if subscription.plan.max_requests_per_month <= 900000:
            usage_percentage = (subscription.requests_used_this_month / subscription.plan.max_requests_per_month) * 100
        
        return render(request, 'subscriptions/dashboard.html', {
            'subscription': subscription,
            'usage_percentage': min(usage_percentage, 100)
        })
    except UserSubscription.DoesNotExist:
        return render(request, 'subscriptions/dashboard.html', {
            'subscription': None,
            'usage_percentage': 0
        })
