"""
Blood Request and Request Response models.
Handles blood donation requests, emergency broadcasts,
and donor-to-request matching with status tracking.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class BloodRequest(models.Model):
    """
    A blood donation request created by a recipient or hospital.
    Contains patient info, location data for geo-matching, and urgency levels.
    """

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    URGENCY_CHOICES = [
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical — Emergency'),
    ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('fulfilled', 'Fulfilled'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blood_requests'
    )
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    patient_name = models.CharField(max_length=100)
    hospital_name = models.CharField(max_length=200)
    hospital_address = models.TextField()
    units_required = models.PositiveIntegerField(default=1, help_text='Number of units needed.')
    units_fulfilled = models.PositiveIntegerField(default=0)
    urgency_level = models.CharField(
        max_length=20, choices=URGENCY_CHOICES, default='normal'
    )
    required_before = models.DateField(
        help_text='Blood needed before this date.'
    )
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True,
        help_text='Hospital/request location latitude.'
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True,
        help_text='Hospital/request location longitude.'
    )
    prescription = models.FileField(
        upload_to='prescriptions/%Y/%m/',
        blank=True, null=True,
        help_text='Optional prescription upload (PDF/Image).'
    )
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='open'
    )
    is_emergency = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Blood Request'
        verbose_name_plural = 'Blood Requests'
        ordering = ['-is_emergency', '-created_at']

    def __str__(self):
        return f'{self.blood_group} — {self.patient_name} ({self.get_urgency_level_display()})'

    def save(self, *args, **kwargs):
        # Automatically flag emergency requests
        if self.urgency_level == 'critical':
            self.is_emergency = True
        # Check if fulfilled
        if self.units_fulfilled >= self.units_required and self.status == 'in_progress':
            self.status = 'fulfilled'
        # Check if expired
        if self.required_before < timezone.now().date() and self.status == 'open':
            self.status = 'expired'
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status in ('open', 'in_progress')

    @property
    def fulfillment_percentage(self):
        if self.units_required == 0:
            return 100
        return int((self.units_fulfilled / self.units_required) * 100)

    @property
    def days_remaining(self):
        delta = self.required_before - timezone.now().date()
        return max(0, delta.days)


class RequestResponse(models.Model):
    """
    Tracks a donor's response (accept/reject) to a blood request.
    Links donors to specific requests with status tracking.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('donated', 'Donated'),
        ('cancelled', 'Cancelled'),
    ]

    request = models.ForeignKey(
        BloodRequest, on_delete=models.CASCADE, related_name='responses'
    )
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='request_responses'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending'
    )
    responded_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    distance_km = models.DecimalField(
        max_digits=8, decimal_places=2, blank=True, null=True,
        help_text='Distance from donor to request location in km.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('request', 'donor')
        ordering = ['distance_km', '-created_at']

    def __str__(self):
        return f'{self.donor.get_full_name()} → {self.request} [{self.get_status_display()}]'
