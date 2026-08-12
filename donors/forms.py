"""
Donor profile forms.
"""

from django import forms
from .models import DonorProfile


class DonorProfileForm(forms.ModelForm):
    """Form for updating Donor profile details."""

    class Meta:
        model = DonorProfile
        fields = ['blood_group', 'last_donation_date', 'availability_status']
        widgets = {
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'last_donation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'availability_status': forms.Select(attrs={'class': 'form-select'}),
        }
