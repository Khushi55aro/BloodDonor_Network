"""
Donor-specific forms for profile creation and updates.
"""

from django import forms
from .models import DonorProfile, DonorRating


class DonorProfileForm(forms.ModelForm):
    """Form for creating / updating a donor profile."""

    class Meta:
        model = DonorProfile
        fields = [
            'blood_group', 'gender', 'age', 'weight',
            'medical_conditions', 'last_donation_date',
            'availability_status',
            'emergency_contact_name', 'emergency_contact_phone'
        ]
        widgets = {
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 120}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'step': '0.1'}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List any medical conditions...'}),
            'last_donation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'availability_status': forms.Select(attrs={'class': 'form-select'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency contact name'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency contact phone'}),
        }


class DonorRatingForm(forms.ModelForm):
    """Form for rating a donor."""
    class Meta:
        model = DonorRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 5}),
            'comment': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Share your experience...'}),
        }
