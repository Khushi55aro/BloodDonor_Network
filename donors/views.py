"""
Views for donor profiles, eligibility, and history.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import DonorProfile
from .forms import DonorProfileForm


@login_required
def donor_dashboard_view(request):
    """Specific dashboard for donors."""
    if not request.user.is_donor:
        return redirect('dashboard:index')

    donor_profile = get_object_or_404(DonorProfile, user=request.user)
    
    context = {
        'donor': donor_profile,
        'is_eligible': donor_profile.is_eligible,
        'eligibility_reasons': donor_profile.eligibility_reasons,
    }
    return render(request, 'donors/dashboard.html', context)


@login_required
def donor_profile_edit_view(request):
    """Edit specific donor details like blood group, medical conditions."""
    if not request.user.is_donor:
        return redirect('dashboard:index')

    donor_profile = get_object_or_404(DonorProfile, user=request.user)
    
    if request.method == 'POST':
        form = DonorProfileForm(request.POST, instance=donor_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your donor profile has been updated.')
            return redirect('donors:dashboard')
    else:
        form = DonorProfileForm(instance=donor_profile)

    return render(request, 'donors/profile_edit.html', {'form': form})
