from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from background_requests.models import Request, Report
from subscriptions.models import UserSubscription

@login_required
def submit_request_page(request):
    try:
        subscription = UserSubscription.objects.get(user=request.user)
    except UserSubscription.DoesNotExist:
        messages.error(request, 'Please select a plan first')
        return redirect('subscriptions:plans-page')
    
    if not subscription.plan:
        messages.error(request, 'Please select a plan first')
        return redirect('subscriptions:plans-page')
    
    if not subscription.can_make_request:
        messages.error(request, 'No reports available. Please purchase more reports.')
        return redirect('subscriptions:purchase-page')
    
    if request.method == 'POST':
        try:
            bg_request = Request.objects.create(
                user=request.user,
                name=request.POST.get('name'),
                email=request.POST.get('email'),
                phone_number=request.POST.get('phone_number'),
                dob=request.POST.get('dob'),
                city=request.POST.get('city'),
                state=request.POST.get('state'),
                status='Pending'
            )
            
            subscription.increment_usage()
            
            messages.success(request, 'Request submitted successfully!')
            return redirect('requests:request-success', request_id=bg_request.id)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
    
    return render(request, 'requests/submit_request.html', {
        'subscription': subscription
    })


@login_required
def request_success_page(request, request_id):
    request_obj = get_object_or_404(Request, id=request_id, user=request.user)
    return render(request, 'requests/request_success.html', {
        'request_obj': request_obj
    })


@login_required
def view_report_page(request, request_id):
    request_obj = get_object_or_404(Request, id=request_id, user=request.user)
    
    report = None
    if hasattr(request_obj, 'report'):
        report = request_obj.report
    
    return render(request, 'requests/view_report.html', {
        'request_obj': request_obj,
        'report': report
    })
