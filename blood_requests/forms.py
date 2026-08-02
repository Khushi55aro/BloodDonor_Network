"""
Blood request forms.
"""

from django import forms
from .models import BloodRequest
from django.utils import timezone

class BloodRequestForm(forms.ModelForm):
    """Form for creating a new blood request."""

    class Meta:
        model = BloodRequest
        fields = [
            'blood_group', 'patient_name', 'hospital_name',
            'hospital_address', 'units_required', 'urgency_level',
            'required_before', 'latitude', 'longitude',
            'prescription', 'notes'
        ]
        widgets = {
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'patient_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Patient Full Name'}),
            'hospital_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hospital / Blood Bank Name'}),
            'hospital_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Full address of the hospital'}),
            'units_required': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'value': 1}),
            'urgency_level': forms.Select(attrs={'class': 'form-select'}),
            'required_before': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001', 'id': 'id_req_latitude'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0000001', 'id': 'id_req_longitude'}),
            'prescription': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes...'}),
        }
        def clean_required_before(self):
            required_before = self.cleaned_data.get("required_before")

            if required_before < timezone.now().date():
                raise forms.ValidationError("Required date cannot be in the past.")

            return required_before


def clean_units_required(self):
    units = self.cleaned_data.get("units_required")

    if units < 1:
        raise forms.ValidationError(
            "Units required must be at least 1."
        )

    return units



class BloodRequestSearchForm(forms.Form):
    """Search / filter form for finding blood requests or donors."""
    BLOOD_GROUP_CHOICES = [('', 'All Blood Groups')] + BloodRequest.BLOOD_GROUP_CHOICES

    blood_group = forms.ChoiceField(
        choices=BLOOD_GROUP_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    city = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'})
    )
    state = forms.CharField(
        max_length=100, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'})
    )
    max_distance = forms.IntegerField(
        required=False, min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max distance (km)'})
    )
    urgency = forms.ChoiceField(
        choices=[('', 'All')] + BloodRequest.URGENCY_CHOICES, required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
