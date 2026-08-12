"""
Accounts views for registration, authentication, profile management, and dashboard routing.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import (
    DonorRegistrationForm,
    RecipientRegistrationForm,
    UserLoginForm,
    UserProfileForm,
)
from donors.models import DonorProfile
from recipients.models import RecipientProfile


def choose_role_view(request):
    """Display Choose Role page (Donor or Recipient)."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    return render(request, 'accounts/choose_role.html')


def donor_register_view(request):
    """Handle Donor Registration."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create associated DonorProfile
            DonorProfile.objects.create(user=user)
            messages.success(request, 'Donor registration successful! Please log in to complete your profile.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = DonorRegistrationForm()

    return render(request, 'accounts/register_donor.html', {'form': form})


def recipient_register_view(request):
    """Handle Recipient Registration."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = RecipientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create associated RecipientProfile
            RecipientProfile.objects.create(user=user)
            messages.success(request, 'Recipient registration successful! Please log in to continue.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Registration failed. Please correct the errors below.')
    else:
        form = RecipientRegistrationForm()

    return render(request, 'accounts/register_recipient.html', {'form': form})


def login_view(request):
    """Handle User Login."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle User Logout."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')


@login_required
def profile_view(request):
    """View and update general user profile."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile details have been updated.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def dashboard_router_view(request):
    """
    Role-based dashboard router.
    Admin -> Django Admin (/admin/)
    Donor -> Donor Dashboard
    Recipient -> Recipient Dashboard
    """
    user = request.user
    if user.is_staff or user.is_superuser:
        return redirect('/admin/')
    elif user.is_donor:
        return redirect('donors:dashboard')
    elif user.is_recipient:
        return redirect('recipients:dashboard')
    else:
        return redirect('core:home')
