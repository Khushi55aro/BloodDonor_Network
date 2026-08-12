"""
DonorProfile model with blood donation eligibility logic and 90-day cooldown period.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class DonorProfile(models.Model):
    """
    Simple profile for blood donors.
    Eligibility rule: LAST DONATION DATE + 90 DAYS COOLDOWN.
    """

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('unavailable', 'Unavailable'),
    ]

    COOLDOWN_DAYS = 90  # Standard 90-day cooldown period

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='donor_profile'
    )
    blood_group = models.CharField(
        max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True, null=True
    )
    last_donation_date = models.DateField(
        blank=True, null=True,
        help_text='Date of last blood donation.'
    )
    availability_status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default='available'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Donor Profile'
        verbose_name_plural = 'Donor Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} ({self.blood_group or "No Blood Group"})'

    @property
    def next_eligible_date(self):
        """
        Calculate next eligible donation date.
        Formula: last_donation_date + 90 days.
        """
        if not self.last_donation_date:
            return None
        return self.last_donation_date + timedelta(days=self.COOLDOWN_DAYS)

    @property
    def remaining_cooldown_days(self):
        """
        Calculate remaining cooldown days.
        Returns 0 if eligible.
        """
        if not self.last_donation_date:
            return 0
        today = timezone.now().date()
        remaining = (self.next_eligible_date - today).days
        return max(0, remaining)

    @property
    def is_eligible(self):
        """
        Donor is eligible if:
        1. Availability status is 'available'
        2. Remaining cooldown days is 0 (last donation was 90+ days ago or never)
        """
        if self.availability_status == 'unavailable':
            return False
        if self.remaining_cooldown_days > 0:
            return False
        return True

    @property
    def eligibility_status_text(self):
        """Human readable eligibility status message."""
        if self.availability_status == 'unavailable':
            return 'Unavailable (Disabled by user)'
        if self.remaining_cooldown_days > 0:
            return f'Ineligible (Cooldown active: {self.remaining_cooldown_days} day(s) remaining. Next eligible: {self.next_eligible_date.strftime("%d %b %Y")})'
        return 'Eligible to Donate'
