"""
Accounts views for authentication, registration, and profile management.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import (
    DonorRegistrationForm,
    RecipientRegistrationForm,
    HospitalRegistrationForm,
    UserLoginForm,
    UserProfileForm,
)
from donors.models import DonorProfile
from recipients.models import RecipientProfile
from hospitals.models import HospitalProfile


def choose_role_view(request):
    """Display the Choose Role page so users pick Donor / Recipient / Hospital."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return render(request, 'accounts/choose_role.html')


def donor_register_view(request):
    """Handle donor registration."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = DonorRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create donor profile — leave optional fields empty
            DonorProfile.objects.create(user=user)
            messages.success(
                request,
                'Registration successful! Please log in to continue.'
            )
            return redirect('accounts:login')
        else:
            messages.error(request, 'Registration failed. Please check the errors below.')
    else:
        form = DonorRegistrationForm()

    return render(request, 'accounts/register_donor.html', {'form': form})


def recipient_register_view(request):
    """Handle recipient registration."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = RecipientRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create recipient profile — leave optional fields empty
            RecipientProfile.objects.create(user=user)
            messages.success(
                request,
                'Registration successful! Please log in to continue.'
            )
            return redirect('accounts:login')
        else:
            messages.error(request, 'Registration failed. Please check the errors below.')
    else:
        form = RecipientRegistrationForm()

    return render(request, 'accounts/register_recipient.html', {'form': form})


def hospital_register_view(request):
    """Handle hospital registration."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = HospitalRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create hospital profile with the name from the form
            HospitalProfile.objects.create(
                user=user,
                hospital_name=form.cleaned_data['hospital_name'],
            )
            messages.success(
                request,
                'Registration successful! Please log in to continue.'
            )
            return redirect('accounts:login')
        else:
            messages.error(request, 'Registration failed. Please check the errors below.')
    else:
        form = HospitalRegistrationForm()

    return render(request, 'accounts/register_hospital.html', {'form': form})


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.username}!')

                # Redirect to ?next= if present, otherwise role-based dashboard
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('dashboard:index')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been successfully logged out.')
    return redirect('core:home')


@login_required
def profile_view(request):
    """View and update general user profile settings."""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})
