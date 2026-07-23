"""
Hospital Profile model for the Blood Donor Network.
"""

from django.db import models
from django.conf import settings


class HospitalProfile(models.Model):
    """Profile for registered hospitals with blood bank facilities."""

    HOSPITAL_TYPE_CHOICES = [
        ('government', 'Government Hospital'),
        ('private', 'Private Hospital'),
        ('clinic', 'Clinic'),
        ('blood_bank', 'Blood Bank'),
        ('ngo', 'NGO / Trust'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hospital_profile'
    )
    hospital_name = models.CharField(max_length=200)
    registration_number = models.CharField(
        max_length=50, unique=True, blank=True, null=True,
        help_text='Hospital registration / license number.'
    )
    hospital_type = models.CharField(
        max_length=20, choices=HOSPITAL_TYPE_CHOICES, default='government'
    )
    website = models.URLField(blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    total_beds = models.PositiveIntegerField(default=0)
    has_blood_bank = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    total_requests = models.PositiveIntegerField(default=0)
    total_donations_facilitated = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Hospital Profile'
        verbose_name_plural = 'Hospital Profiles'
        ordering = ['hospital_name']

    def __str__(self):
        return self.hospital_name
