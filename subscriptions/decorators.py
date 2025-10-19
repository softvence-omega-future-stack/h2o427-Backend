from functools import wraps
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from .models import UserSubscription


def subscription_required(feature_name=None, increment_usage=True):
    """
    Decorator to check if user has an active subscription and can access a feature.
    
    Args:
        feature_name (str): Name of the feature to check access for
        increment_usage (bool): Whether to increment usage count on successful access
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user is authenticated
            if not request.user or not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Authentication required',
                    'subscription_required': True
                }, status=401)
            
            try:
                subscription = UserSubscription.objects.get(user=request.user)
                
                # Check if subscription is active
                if subscription.status != 'active':
                    return JsonResponse({
                        'error': 'Active subscription required',
                        'subscription_status': subscription.status,
                        'subscription_required': True
                    }, status=403)
                
                # Check if user can make requests this month
                if not subscription.can_make_request:
                    return JsonResponse({
                        'error': 'Monthly request limit exceeded',
                        'requests_used': subscription.requests_used_this_month,
                        'max_requests': subscription.plan.max_requests_per_month,
                        'subscription_required': True
                    }, status=403)
                
                # Check specific feature access if feature_name is provided
                if feature_name:
                    has_feature = subscription.plan.has_feature(feature_name)
                    if not has_feature:
                        return JsonResponse({
                            'error': f'Feature "{feature_name}" not available in your plan',
                            'current_plan': subscription.plan.name,
                            'subscription_required': True
                        }, status=403)
                
                # Increment usage if requested
                if increment_usage:
                    subscription.increment_usage()
                
                # Call the original view
                return view_func(request, *args, **kwargs)
                
            except UserSubscription.DoesNotExist:
                return JsonResponse({
                    'error': 'No subscription found. Please subscribe to access this feature.',
                    'subscription_required': True
                }, status=403)
        
        return wrapper
    return decorator


def require_subscription_plan(min_plan_level=1):
    """
    Decorator to require a minimum subscription plan level.
    
    Args:
        min_plan_level (int): Minimum plan level required (1=Basic, 2=Pro, 3=Enterprise)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return JsonResponse({
                    'error': 'Authentication required',
                    'subscription_required': True
                }, status=401)
            
            try:
                subscription = UserSubscription.objects.get(user=request.user)
                
                if subscription.status != 'active':
                    return JsonResponse({
                        'error': 'Active subscription required',
                        'subscription_required': True
                    }, status=403)
                
                # Check plan level
                plan_levels = {
                    'basic': 1,
                    'pro': 2,
                    'enterprise': 3
                }
                
                current_level = plan_levels.get(subscription.plan.plan_type.lower(), 0)
                
                if current_level < min_plan_level:
                    required_plans = [k for k, v in plan_levels.items() if v >= min_plan_level]
                    return JsonResponse({
                        'error': f'This feature requires a {" or ".join(required_plans)} plan',
                        'current_plan': subscription.plan.plan_type,
                        'required_level': min_plan_level,
                        'subscription_required': True
                    }, status=403)
                
                return view_func(request, *args, **kwargs)
                
            except UserSubscription.DoesNotExist:
                return JsonResponse({
                    'error': 'No subscription found',
                    'subscription_required': True
                }, status=403)
        
        return wrapper
    return decorator


class SubscriptionMiddleware:
    """
    Middleware to add subscription information to request object
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add subscription info to request
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                subscription = UserSubscription.objects.get(user=request.user)
                request.subscription = subscription
                request.has_active_subscription = subscription.status == 'active'
                request.can_make_request = subscription.can_make_request
            except UserSubscription.DoesNotExist:
                request.subscription = None
                request.has_active_subscription = False
                request.can_make_request = False
        else:
            request.subscription = None
            request.has_active_subscription = False
            request.can_make_request = False

        response = self.get_response(request)
        return response


# For REST Framework class-based views
class SubscriptionPermission:
    """
    Permission class for Django REST Framework to check subscription access
    """
    def __init__(self, feature_name=None, increment_usage=True):
        self.feature_name = feature_name
        self.increment_usage = increment_usage
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            
            if subscription.status != 'active':
                return False
            
            if not subscription.can_make_request:
                return False
            
            if self.feature_name:
                if not subscription.plan.has_feature(self.feature_name):
                    return False
            
            if self.increment_usage:
                subscription.increment_usage()
            
            return True
            
        except UserSubscription.DoesNotExist:
            return False