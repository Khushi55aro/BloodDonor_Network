"""
Custom User model with role-based authorization for Blood Donor Network.
Roles: Admin, Donor, Recipient.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model with role-based access control.
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        DONOR = 'DONOR', 'Donor'
        RECIPIENT = 'RECIPIENT', 'Recipient'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DONOR,
        help_text='User role determines access permissions.'
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True,
        help_text='Latitude coordinate for location matching.'
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True,
        help_text='Longitude coordinate for location matching.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_staff or self.is_superuser

    @property
    def is_donor(self):
        return self.role == self.Role.DONOR

    @property
    def is_recipient(self):
        return self.role == self.Role.RECIPIENT
