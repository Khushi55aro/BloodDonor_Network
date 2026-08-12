"""
Blood request form.
"""

from django import forms
from .models import BloodRequest


class BloodRequestForm(forms.ModelForm):
    """Form for creating a new blood donation request."""

    class Meta:
        model = BloodRequest
        fields = [
            'blood_group',
            'units_required',
            'address',
            'latitude',
            'longitude',
            'is_emergency'
        ]

        widgets = {
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'units_required': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter full hospital/location address'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001'}),
            'is_emergency': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_units_required(self):
        units = self.cleaned_data.get("units_required")
        if units is None or units < 1:
            raise forms.ValidationError("Units required must be at least 1.")
        return units