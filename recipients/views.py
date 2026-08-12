"""
Views for recipient dashboard and recipient profile management.
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import RecipientProfile
from .forms import RecipientProfileForm


@login_required
def recipient_dashboard_view(request):
    """Dashboard for recipients listing their created blood requests."""
    if not request.user.is_recipient:
        return redirect('accounts:dashboard')

    recipient_profile, _ = RecipientProfile.objects.get_or_create(user=request.user)

    # Get requests created by this recipient
    my_requests = request.user.blood_requests.all().order_by('-created_at')

    context = {
        'recipient': recipient_profile,
        'my_requests': my_requests,
    }
    return render(request, 'recipients/dashboard.html', context)


@login_required
def recipient_profile_edit_view(request):
    """Edit recipient details (needed blood group)."""
    if not request.user.is_recipient:
        return redirect('accounts:dashboard')

    recipient_profile, _ = RecipientProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = RecipientProfileForm(request.POST, instance=recipient_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recipient profile updated successfully!')
            return redirect('recipients:dashboard')
    else:
        form = RecipientProfileForm(instance=recipient_profile)

    return render(request, 'recipients/profile_edit.html', {'form': form})
