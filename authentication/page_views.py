from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from authentication.models import User
from subscriptions.models import UserSubscription

def register_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        full_name = request.POST.get('full_name', '')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'authentication/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'authentication/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken')
            return render(request, 'authentication/register.html')
        
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                full_name=full_name
            )
            messages.success(request, 'Registration successful! Please login.')
            return redirect('auth:login-page')
        except Exception as e:
            messages.error(request, f'Registration failed: {str(e)}')
    
    return render(request, 'authentication/register.html')


def login_page(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('subscriptions:my-dashboard')
        else:
            messages.error(request, 'Invalid email or password')
    
    return render(request, 'authentication/login.html')


def logout_page(request):
    logout(request)
    messages.success(request, 'Logged out successfully')
    return redirect('auth:login-page')
