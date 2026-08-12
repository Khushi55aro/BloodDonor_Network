"""
BloodRequest and RequestResponse models.
Handles blood donation requests, emergency broadcasts, and donor-to-request matching.
"""

from django.db import models
from django.conf import settings


class BloodRequest(models.Model):
    """
    A blood donation request created by a recipient.
    """

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Fulfilled', 'Fulfilled'),
        ('Cancelled', 'Cancelled'),
    ]

    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blood_requests'
    )
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES)
    units_required = models.PositiveIntegerField(default=1, help_text='Number of units needed.')
    address = models.TextField(help_text='Address or hospital location where blood is needed.')
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True,
        help_text='Latitude for Geo-matching.'
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True,
        help_text='Longitude for Geo-matching.'
    )
    is_emergency = models.BooleanField(default=False, help_text='Flag for urgent emergency broadcast.')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Open'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Blood Request'
        verbose_name_plural = 'Blood Requests'
        ordering = ['-is_emergency', '-created_at']

    def __str__(self):
        emergency_tag = "[EMERGENCY] " if self.is_emergency else ""
        return f'{emergency_tag}{self.blood_group} - {self.units_required} unit(s) by {self.requester.username}'

    @property
    def is_active(self):
        return self.status == 'Open'


class RequestResponse(models.Model):
    """
    Tracks a matched donor's response (Accept / Reject) to a blood request.
    """

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
    ]

    request = models.ForeignKey(
        BloodRequest, on_delete=models.CASCADE, related_name='responses'
    )
    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='request_responses'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('request', 'donor')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.donor.username} -> Request #{self.request.id} [{self.status}]'
