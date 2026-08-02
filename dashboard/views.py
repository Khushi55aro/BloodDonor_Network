"""
Views for the routing dashboard and full admin analytics & management suite.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import models
from accounts.models import User
from donors.models import DonorProfile
from recipients.models import RecipientProfile
from hospitals.models import HospitalProfile
from blood_requests.models import BloodRequest
from reports.models import DonationRecord


@login_required
def dashboard_router_view(request):
    """
    Routes the logged-in user to their respective role dashboard.
    Admin/Staff -> Custom Admin Dashboard
    Donor -> Donor Dashboard
    Recipient -> Recipient Dashboard
    Hospital -> Hospital Portal
    """
    if request.user.is_admin or request.user.is_staff:
        return redirect('dashboard:admin_dashboard')
    elif request.user.is_donor:
        return redirect('donors:dashboard')
    elif request.user.is_recipient:
        return redirect('recipients:dashboard')
    elif request.user.is_hospital:
        return redirect('hospitals:portal')
    else:
        return redirect('core:home')


@staff_member_required
def admin_dashboard_view(request):
    """Admin analytics dashboard with statistics, charts, and system control."""
    # Summary Statistics
    total_users = User.objects.count()
    total_donors = DonorProfile.objects.count()
    total_recipients = RecipientProfile.objects.count()
    total_hospitals = HospitalProfile.objects.count()
    active_requests = BloodRequest.objects.filter(status__in=['open', 'in_progress']).count()
    completed_donations = DonationRecord.objects.count()

    # Blood Group Distribution for Donors
    bg_data = {}
    for choice in DonorProfile.BLOOD_GROUP_CHOICES:
        bg = choice[0]
        bg_data[bg] = DonorProfile.objects.filter(blood_group=bg).count()

    # Recent emergency requests
    emergencies = BloodRequest.objects.filter(is_emergency=True).order_by('-created_at')[:5]

    # Recent users
    recent_users = User.objects.all().order_by('-date_joined')[:5]

    context = {
        'total_users': total_users,
        'total_donors': total_donors,
        'total_recipients': total_recipients,
        'total_hospitals': total_hospitals,
        'active_requests': active_requests,
        'completed_donations': completed_donations,
        'bg_labels': list(bg_data.keys()),
        'bg_counts': list(bg_data.values()),
        'emergencies': emergencies,
        'recent_users': recent_users,
    }
    return render(request, 'dashboard/admin.html', context)


@staff_member_required
def admin_manage_users_view(request):
    """Staff management page for searching, filtering, and performing CRUD on users."""
    role_filter = request.GET.get('role', '')
    query = request.GET.get('q', '')

    users = User.objects.filter(is_superuser=False).order_by('-date_joined')

    if role_filter:
        users = users.filter(role=role_filter)

    if query:
        users = users.filter(
            models.Q(username__icontains=query) |
            models.Q(email__icontains=query) |
            models.Q(first_name__icontains=query) |
            models.Q(last_name__icontains=query) |
            models.Q(city__icontains=query)
        )

    context = {
        'users': users,
        'role_filter': role_filter,
        'query': query,
    }
    return render(request, 'dashboard/admin_manage_users.html', context)


@staff_member_required
def admin_toggle_user_status_view(request, user_id):
    """Toggle user active/inactive status."""
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, 'You cannot deactivate your own admin account.')
        return redirect('dashboard:admin_manage_users')

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])

    status_str = 'activated' if target_user.is_active else 'deactivated'
    messages.success(request, f'User {target_user.username} has been {status_str}.')
    return redirect('dashboard:admin_manage_users')


@staff_member_required
def admin_toggle_verification_view(request, entity_type, entity_id):
    """Toggle verification status for Donors or Hospitals."""
    if entity_type == 'donor':
        donor = get_object_or_404(DonorProfile, id=entity_id)
        donor.is_verified = not donor.is_verified
        donor.save(update_fields=['is_verified'])
        messages.success(request, f'Verification status updated for Donor {donor.user.get_full_name()}.')
    elif entity_type == 'hospital':
        hospital = get_object_or_404(HospitalProfile, id=entity_id)
        hospital.is_verified = not hospital.is_verified
        hospital.save(update_fields=['is_verified'])
        messages.success(request, f'Verification status updated for Hospital {hospital.hospital_name}.')

    return redirect(request.META.get('HTTP_REFERER', 'dashboard:admin_dashboard'))


@staff_member_required
def admin_delete_user_view(request, user_id):
    """Delete a user account."""
    target_user = get_object_or_404(User, id=user_id)

    # Prevent deletion of superuser accounts
    if target_user.is_superuser:
        messages.error(request, "Superuser account cannot be deleted.")
        return redirect("dashboard:admin_manage_users")

    if target_user == request.user:
        messages.error(request, 'You cannot delete your own admin account.')
        return redirect('dashboard:admin_manage_users')

    username = target_user.username
    target_user.delete()
    messages.success(request, f'User account {username} deleted successfully.')
    return redirect('dashboard:admin_manage_users')