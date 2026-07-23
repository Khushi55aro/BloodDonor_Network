"""
Recipient Profile model for blood request seekers.
"""

from django.db import models
from django.conf import settings


class RecipientProfile(models.Model):
    """Profile for users seeking blood donations."""

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipient_profile'
    )
    blood_group_needed = models.CharField(
        max_length=5, choices=BLOOD_GROUP_CHOICES,
        blank=True, null=True,
        help_text='Most commonly needed blood group.'
    )
    total_requests = models.PositiveIntegerField(default=0)
    total_fulfilled = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Recipient Profile'
        verbose_name_plural = 'Recipient Profiles'

    def __str__(self):
        return f'{self.user.get_full_name()} (Recipient)'
