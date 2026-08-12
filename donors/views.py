"""
Views for donor profile, dashboard, eligibility display, and availability toggle.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DonorProfile
from .forms import DonorProfileForm
from blood_requests.models import RequestResponse


@login_required
def donor_dashboard_view(request):
    """Dashboard for donors showing eligibility status and matching requests."""
    if not request.user.is_donor:
        return redirect('accounts:dashboard')

    donor_profile, _ = DonorProfile.objects.get_or_create(user=request.user)

    # Incoming request notifications / responses for this donor
    incoming_responses = RequestResponse.objects.filter(donor=request.user).select_related(
        'request', 'request__requester'
    ).order_by('-created_at')[:10]

    context = {
        'donor': donor_profile,
        'is_eligible': donor_profile.is_eligible,
        'eligibility_status_text': donor_profile.eligibility_status_text,
        'incoming_responses': incoming_responses,
    }
    return render(request, 'donors/dashboard.html', context)


@login_required
def toggle_availability_view(request):
    """Toggle donor availability between Available and Unavailable."""
    if not request.user.is_donor:
        return redirect('accounts:dashboard')

    donor_profile = get_object_or_404(DonorProfile, user=request.user)

    if donor_profile.availability_status == 'available':
        donor_profile.availability_status = 'unavailable'
        messages.warning(request, 'Your status is now set to Unavailable.')
    else:
        donor_profile.availability_status = 'available'
        messages.success(request, 'Your status is now set to Available.')

    donor_profile.save(update_fields=['availability_status'])
    return redirect('donors:dashboard')


@login_required
def donor_profile_edit_view(request):
    """Edit donor details (blood group, last donation date, availability)."""
    if not request.user.is_donor:
        return redirect('accounts:dashboard')

    donor_profile, _ = DonorProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = DonorProfileForm(request.POST, instance=donor_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Donor profile updated successfully!')
            return redirect('donors:dashboard')
        else:
            messages.error(request, 'Failed to update donor profile. Check form errors below.')
    else:
        form = DonorProfileForm(instance=donor_profile)

    return render(request, 'donors/profile_edit.html', {'form': form, 'donor': donor_profile})
