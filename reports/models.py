"""
Reports models — tracks completed donations and generates certificates.
"""

from django.db import models
from django.conf import settings
import uuid


class DonationRecord(models.Model):
    """
    Official record of a completed blood donation.
    Used for reporting, certificates, and donation history.
    """

    donor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='donation_records'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='received_donations'
    )
    blood_request = models.ForeignKey(
        'blood_requests.BloodRequest',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='donation_records'
    )
    hospital_name = models.CharField(max_length=200)
    blood_group = models.CharField(max_length=5)
    units_donated = models.PositiveIntegerField(default=1)
    donation_date = models.DateField()
    certificate_id = models.CharField(
        max_length=50, unique=True, blank=True,
        help_text='Unique certificate ID for verification.'
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='verified_donations'
    )
    is_verified = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Donation Record'
        verbose_name_plural = 'Donation Records'
        ordering = ['-donation_date']

    def __str__(self):
        return f'{self.donor.get_full_name()} — {self.blood_group} on {self.donation_date}'

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = f'CERT-{uuid.uuid4().hex[:10].upper()}'
        super().save(*args, **kwargs)
