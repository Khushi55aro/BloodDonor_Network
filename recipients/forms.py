"""
Recipient profile forms.
"""

from django import forms
from .models import RecipientProfile


class RecipientProfileForm(forms.ModelForm):
    """Form for updating Recipient profile details."""

    class Meta:
        model = RecipientProfile
        fields = ['blood_group_needed']
        widgets = {
            'blood_group_needed': forms.Select(attrs={'class': 'form-select'}),
        }
