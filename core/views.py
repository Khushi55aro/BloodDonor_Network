"""
Core public page views.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm
from accounts.models import User
from donors.models import DonorProfile
from blood_requests.models import BloodRequest


def home_view(request):
    """Home page."""
    stats = {
        'total_donors': DonorProfile.objects.count(),
        'total_recipients': User.objects.filter(role='RECIPIENT').count(),
        'active_requests': BloodRequest.objects.filter(status='Open').count(),
    }
    return render(request, 'core/home.html', {'stats': stats})


def about_view(request):
    """About Us page."""
    return render(request, 'core/about.html')


def contact_view(request):
    """Contact page."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('core:contact')
    else:
        form = ContactForm()

    return render(request, 'core/contact.html', {'form': form})
