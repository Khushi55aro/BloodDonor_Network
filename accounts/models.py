"""
Custom User model with role-based authentication for the Blood Donor Network.
Supports four roles: Admin, Donor, Recipient, Hospital.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Extended User model with role-based access control.
    Every user has exactly one role that determines their dashboard and permissions.
    """

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        DONOR = 'DONOR', 'Donor'
        RECIPIENT = 'RECIPIENT', 'Recipient'
        HOSPITAL = 'HOSPITAL', 'Hospital'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.DONOR,
        help_text='User role determines dashboard and permissions.'
    )
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_photo = models.ImageField(
        upload_to='profile_photos/%Y/%m/',
        blank=True,
        null=True,
        help_text='Profile photo (max 5MB).'
    )
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True,
        help_text='GPS Latitude coordinate.'
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, blank=True, null=True,
        help_text='GPS Longitude coordinate.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_donor(self):
        return self.role == self.Role.DONOR

    @property
    def is_recipient(self):
        return self.role == self.Role.RECIPIENT

    @property
    def is_hospital(self):
        return self.role == self.Role.HOSPITAL

    @property
    def profile_completion_percentage(self):
        """Calculate how complete the user's profile is."""
        fields = [
            self.first_name, self.last_name, self.email, self.phone,
            self.profile_photo, self.date_of_birth, self.address,
            self.city, self.state, self.pincode, self.latitude, self.longitude
        ]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)
