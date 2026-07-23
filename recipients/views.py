"""
Views for recipient dashboard and profiles.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import RecipientProfile
from .forms import RecipientProfileForm


@login_required
def recipient_dashboard_view(request):
    """Specific dashboard for recipients."""
    if not request.user.is_recipient:
        return redirect('dashboard:index')

    recipient_profile = get_object_or_404(RecipientProfile, user=request.user)
    requests = request.user.blood_requests.all().order_by('-created_at')[:5]
    
    context = {
        'recipient': recipient_profile,
        'recent_requests': requests,
    }
    return render(request, 'recipients/dashboard.html', context)


@login_required
def recipient_profile_edit_view(request):
    """Edit specific recipient details."""
    if not request.user.is_recipient:
        return redirect('dashboard:index')

    recipient_profile = get_object_or_404(RecipientProfile, user=request.user)
    
    if request.method == 'POST':
        form = RecipientProfileForm(request.POST, instance=recipient_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recipient profile has been updated.')
            return redirect('recipients:dashboard')
    else:
        form = RecipientProfileForm(instance=recipient_profile)

    return render(request, 'recipients/profile_edit.html', {'form': form})
