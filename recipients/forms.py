"""
Recipient-specific forms.
"""

from django import forms
from .models import RecipientProfile


class RecipientProfileForm(forms.ModelForm):

    class Meta:
        model = RecipientProfile
        fields = ['blood_group_needed']
        widgets = {
            'blood_group_needed': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_blood_group_needed(self):
        blood_group = self.cleaned_data.get("blood_group_needed")

        if not blood_group:
            raise forms.ValidationError(
                "Please select a blood group."
            )

        return blood_group
