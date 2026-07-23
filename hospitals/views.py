"""
Views for hospital portal and profiles.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import HospitalProfile
from .forms import HospitalProfileForm


@login_required
def hospital_portal_view(request):
    """Specific dashboard for hospitals."""
    if not request.user.is_hospital:
        return redirect('dashboard:index')

    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    requests = request.user.blood_requests.all().order_by('-created_at')[:10]
    
    context = {
        'hospital': hospital_profile,
        'recent_requests': requests,
    }
    return render(request, 'hospitals/portal.html', context)


@login_required
def hospital_profile_edit_view(request):
    """Edit specific hospital details."""
    if not request.user.is_hospital:
        return redirect('dashboard:index')

    hospital_profile = get_object_or_404(HospitalProfile, user=request.user)
    
    if request.method == 'POST':
        form = HospitalProfileForm(request.POST, instance=hospital_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hospital profile has been updated.')
            return redirect('hospitals:portal')
    else:
        form = HospitalProfileForm(instance=hospital_profile)

    return render(request, 'hospitals/profile_edit.html', {'form': form})
