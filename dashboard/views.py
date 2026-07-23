"""
Views for the routing dashboard and admin analytics dashboard.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
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
    Admin -> Django Admin
    Donor -> Donor Dashboard
    Recipient -> Recipient Dashboard
    Hospital -> Hospital Portal
    """
    if request.user.is_admin or request.user.is_staff:
        return redirect('admin:index')
    elif request.user.is_donor:
        return redirect('donors:dashboard')
    elif request.user.is_recipient:
        return redirect('recipients:dashboard')
    elif request.user.is_hospital:
        return redirect('hospitals:portal')
    else:
        # Fallback
        return redirect('core:home')


@staff_member_required
def admin_dashboard_view(request):
    """Admin analytics dashboard with Chart.js data."""
    
    # Summary Statistics
    total_users = User.objects.count()
    total_donors = DonorProfile.objects.count()
    total_hospitals = HospitalProfile.objects.count()
    active_requests = BloodRequest.objects.filter(status__in=['open', 'in_progress']).count()
    completed_donations = DonationRecord.objects.count()
    
    # Blood Group Distribution for Donors
    bg_data = {}
    for choice in DonorProfile.BLOOD_GROUP_CHOICES:
        bg = choice[0]
        bg_data[bg] = DonorProfile.objects.filter(blood_group=bg).count()
        
    # Recent emergency requests
    emergencies = BloodRequest.objects.filter(is_emergency=True, status__in=['open', 'in_progress']).order_by('-created_at')[:5]

    context = {
        'total_users': total_users,
        'total_donors': total_donors,
        'total_hospitals': total_hospitals,
        'active_requests': active_requests,
        'completed_donations': completed_donations,
        'bg_labels': list(bg_data.keys()),
        'bg_counts': list(bg_data.values()),
        'emergencies': emergencies,
    }
    return render(request, 'dashboard/admin.html', context)
