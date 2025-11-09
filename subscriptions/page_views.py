from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from subscriptions.models import SubscriptionPlan, UserSubscription
from background_requests.models import Request

@login_required
def plans_page(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return render(request, 'subscriptions/select_plan.html', {'plans': plans})


@login_required
def select_plan(request):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            subscription, created = UserSubscription.objects.get_or_create(
                user=request.user,
                defaults={'plan': plan}
            )
            
            if not created:
                subscription.plan = plan
                subscription.save()
            
            messages.success(request, f'Plan "{plan.name}" selected successfully!')
            return redirect('subscriptions:my-dashboard')
        except SubscriptionPlan.DoesNotExist:
            messages.error(request, 'Invalid plan selected')
    
    return redirect('subscriptions:plans-page')


@login_required
def purchase_page(request):
    try:
        subscription = UserSubscription.objects.get(user=request.user)
    except UserSubscription.DoesNotExist:
        messages.error(request, 'Please select a plan first')
        return redirect('subscriptions:plans-page')
    
    stripe_public_key = settings.STRIPE_PUBLISHABLE_KEY
    
    return render(request, 'subscriptions/purchase.html', {
        'subscription': subscription,
        'stripe_public_key': stripe_public_key
    })


@login_required
def my_dashboard(request):
    try:
        subscription = UserSubscription.objects.select_related('plan').get(user=request.user)
    except UserSubscription.DoesNotExist:
        subscription = None
    
    requests = Request.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'subscriptions/my_dashboard.html', {
        'subscription': subscription,
        'requests': requests
    })
