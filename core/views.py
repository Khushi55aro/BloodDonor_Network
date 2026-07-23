"""
Core views for public pages.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import FAQ, Testimonial, SuccessStory
from .forms import ContactForm
from accounts.models import User
from donors.models import DonorProfile
from blood_requests.models import BloodRequest


def home_view(request):
    """Home page with statistics and testimonials."""
    testimonials = Testimonial.objects.filter(is_active=True)[:3]
    success_stories = SuccessStory.objects.filter(is_active=True)[:3]
    
    # Stats
    stats = {
        'total_users': User.objects.count(),
        'total_donors': DonorProfile.objects.count(),
        'lives_saved': BloodRequest.objects.filter(status='fulfilled').count() * 3, # Assuming 1 donation saves up to 3 lives
    }
    
    context = {
        'testimonials': testimonials,
        'success_stories': success_stories,
        'stats': stats,
    }
    return render(request, 'core/home.html', context)


def about_view(request):
    """About Us page."""
    return render(request, 'core/about.html')


def contact_view(request):
    """Contact page with form."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your message has been sent successfully. We will get back to you soon!')
            return redirect('core:contact')
    else:
        form = ContactForm()
        
    return render(request, 'core/contact.html', {'form': form})


def faq_view(request):
    """FAQ page."""
    faqs = FAQ.objects.filter(is_active=True).order_by('order')
    return render(request, 'core/faq.html', {'faqs': faqs})
