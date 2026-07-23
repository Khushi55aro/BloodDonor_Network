"""
Hospital-specific forms.
"""

from django import forms
from .models import HospitalProfile


class HospitalProfileForm(forms.ModelForm):
    """Form for creating / updating a hospital profile."""

    class Meta:
        model = HospitalProfile
        fields = [
            'hospital_name', 'registration_number', 'hospital_type',
            'phone', 'website', 'total_beds', 'has_blood_bank', 'description'
        ]
        widgets = {
            'hospital_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hospital Name'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Registration / License Number'}),
            'hospital_type': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact Phone'}),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'total_beds': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'has_blood_bank': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'About the hospital...'}),
        }
