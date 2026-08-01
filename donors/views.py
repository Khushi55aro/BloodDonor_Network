"""
Views for donor profiles, eligibility, availability toggle, and dashboard.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DonorProfile
from .forms import DonorProfileForm
from blood_requests.models import RequestResponse, BloodRequest
from blood_requests.utils import BLOOD_COMPATIBILITY
from reports.models import DonationRecord


@login_required
def donor_dashboard_view(request):
    """Specific dashboard for donors."""
    if not request.user.is_donor:
        return redirect('dashboard:index')

    donor_profile, _ = DonorProfile.objects.get_or_create(user=request.user)

    # Incoming requests specifically matched for this donor
    incoming_responses = RequestResponse.objects.filter(donor=request.user).select_related(
        'request', 'request__requester'
    ).order_by('-created_at')[:5]

    # Nearby emergency requests
    donor_bg = donor_profile.blood_group
    nearby_emergencies = []
    if donor_bg and request.user.latitude and request.user.longitude:
        can_donate_to = [bg for bg, donors in BLOOD_COMPATIBILITY.items() if donor_bg in donors]
        emergencies = BloodRequest.objects.filter(
            status__in=['open', 'in_progress'],
            is_emergency=True,
            blood_group__in=can_donate_to
        ).order_by('-created_at')[:5]

        for req in emergencies:
            dist = donor_profile.distance_to(req.latitude, req.longitude)
            if dist is not None and dist <= 100:
                req.distance = round(dist, 1)
                nearby_emergencies.append(req)

    # Recent donation history
    donation_history = DonationRecord.objects.filter(donor=request.user).order_by('-donation_date')[:5]

    context = {
        'donor': donor_profile,
        'is_eligible': donor_profile.is_eligible,
        'eligibility_reasons': donor_profile.eligibility_reasons,
        'incoming_responses': incoming_responses,
        'nearby_emergencies': nearby_emergencies,
        'donation_history': donation_history,
    }
    return render(request, 'donors/dashboard.html', context)


@login_required
def toggle_availability_view(request):
    """Toggle donor availability between available and unavailable."""
    if not request.user.is_donor:
        return redirect('dashboard:index')

    donor_profile = get_object_or_404(DonorProfile, user=request.user)
    
    if donor_profile.availability_status == 'available':
        donor_profile.availability_status = 'unavailable'
        messages.warning(request, 'Your availability status has been set to Unavailable.')
    else:
        donor_profile.availability_status = 'available'
        messages.success(request, 'Your availability status has been set to Available.')

    donor_profile.save(update_fields=['availability_status'])
    return redirect('donors:dashboard')


@login_required
def donor_profile_edit_view(request):
    """Edit specific donor details like blood group, medical conditions, last donation date."""
    if not request.user.is_donor:
        return redirect('dashboard:index')

    donor_profile, _ = DonorProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = DonorProfileForm(request.POST, instance=donor_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your donor profile has been updated successfully!')
            return redirect('donors:dashboard')
        else:
            messages.error(request, 'Failed to update donor profile. Please check the errors below.')
    else:
        form = DonorProfileForm(instance=donor_profile)

    return render(request, 'donors/profile_edit.html', {'form': form, 'donor': donor_profile})
