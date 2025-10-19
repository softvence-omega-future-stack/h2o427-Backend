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
    
    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)

class UserSubscriptionView(APIView):
    """View to manage user's subscription"""
    permission_classes = [permissions.IsAuthenticated]
    
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
    
    def get(self, request):
        payments = PaymentHistory.objects.filter(user=request.user).order_by('-created_at')
        serializer = PaymentHistorySerializer(payments, many=True)
        return Response(serializer.data)

class StripeWebhookView(APIView):
    """View to handle Stripe webhooks"""
    permission_classes = [permissions.AllowAny]
    
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
        if event['type'] == 'payment_intent.succeeded':
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

