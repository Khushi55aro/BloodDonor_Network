"""
Donor Profile model with blood donation eligibility logic,
cooldown calculations, and availability tracking.
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import math


class DonorProfile(models.Model):
    """
    Extended profile for donors with medical info, donation history,
    and automatic eligibility computation based on gender-specific cooldowns.
    """

    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    AVAILABILITY_CHOICES = [
        ('available', 'Available'),
        ('unavailable', 'Unavailable'),
        ('emergency_only', 'Emergency Only'),
    ]

    # Cooldown periods in days
    MALE_COOLDOWN_DAYS = 90
    FEMALE_COOLDOWN_DAYS = 120
    MIN_AGE = 18
    MAX_AGE = 65
    MIN_WEIGHT = 50  # kg

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='donor_profile'
    )
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUP_CHOICES, blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    age = models.PositiveIntegerField(help_text='Age in years', blank=True, null=True)
    weight = models.DecimalField(
        max_digits=5, decimal_places=2,
        help_text='Weight in kg',
        blank=True, null=True
    )
    medical_conditions = models.TextField(
        blank=True, null=True,
        help_text='List any medical conditions that may affect donation eligibility.'
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
    total_donations = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=5.00,
        help_text='Average donor rating (1-5).'
    )
    total_ratings = models.PositiveIntegerField(default=0)
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(
        default=False,
        help_text='Verified by admin after document check.'
    )
    donor_id = models.CharField(
        max_length=20, unique=True, blank=True, null=True,
        help_text='Unique Donor ID for QR codes and certificates.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Donor Profile'
        verbose_name_plural = 'Donor Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.get_full_name()} - {self.blood_group}'

    def save(self, *args, **kwargs):
        # Auto-generate a unique Donor ID if not set
        if not self.donor_id:
            super().save(*args, **kwargs)
            self.donor_id = f'BDN-{self.pk:06d}'
            super().save(update_fields=['donor_id'])
        else:
            super().save(*args, **kwargs)

    @property
    def cooldown_days(self):
        """Return the cooldown period in days based on gender."""
        if self.gender == 'F':
            return self.FEMALE_COOLDOWN_DAYS
        return self.MALE_COOLDOWN_DAYS

    @property
    def next_eligible_date(self):
        """Calculate the next date the donor is eligible to donate."""
        if not self.last_donation_date:
            return None  # Never donated, eligible now
        return self.last_donation_date + timedelta(days=self.cooldown_days)

    @property
    def remaining_cooldown_days(self):
        """Calculate remaining cooldown days. Returns 0 if eligible."""
        if not self.last_donation_date:
            return 0
        next_date = self.next_eligible_date
        today = timezone.now().date()
        remaining = (next_date - today).days
        return max(0, remaining)

    @property
    def is_eligible(self):
        """
        Determine if the donor is currently eligible to donate blood.
        Rules:
        - Age: 18-65
        - Weight: >= 50 kg
        - Cooldown period passed since last donation
        - No disqualifying medical conditions
        - Availability is not 'unavailable'
        """
        # Profile incomplete — not eligible until filled in
        if self.age is None or self.weight is None:
            return False

        # Age check
        if not (self.MIN_AGE <= self.age <= self.MAX_AGE):
            return False

        # Weight check
        if self.weight < self.MIN_WEIGHT:
            return False

        # Cooldown check
        if self.remaining_cooldown_days > 0:
            return False

        # Availability check
        if self.availability_status == 'unavailable':
            return False

        return True

    @property
    def eligibility_reasons(self):
        """Return a list of reasons why the donor is/isn't eligible."""
        reasons = []
        if self.age is None or self.weight is None:
            reasons.append('Profile is incomplete. Please update your blood group, age, and weight.')
            return reasons
        if not (self.MIN_AGE <= self.age <= self.MAX_AGE):
            reasons.append(f'Age must be between {self.MIN_AGE} and {self.MAX_AGE} years.')
        if self.weight < self.MIN_WEIGHT:
            reasons.append(f'Weight must be at least {self.MIN_WEIGHT} kg.')
        if self.remaining_cooldown_days > 0:
            reasons.append(
                f'Cooldown period active. {self.remaining_cooldown_days} days remaining. '
                f'Next eligible: {self.next_eligible_date.strftime("%d %B %Y")}.'
            )
        if self.availability_status == 'unavailable':
            reasons.append('Currently marked as unavailable.')
        return reasons

    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate the great-circle distance between two points on Earth
        using the Haversine formula. Returns distance in kilometers.
        """
        R = 6371  # Earth's radius in km
        lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + \
            math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    def distance_to(self, lat, lon):
        """Calculate distance from this donor to a given location in km."""
        if self.user.latitude and self.user.longitude:
            return self.haversine_distance(
                self.user.latitude, self.user.longitude, lat, lon
            )
        return None

    @property
    def estimated_travel_time(self):
        """Placeholder — in real app, could use a routing API."""
        return None


class DonorRating(models.Model):
    """Rating given to a donor by a recipient after a successful donation."""
    donor = models.ForeignKey(
        DonorProfile, on_delete=models.CASCADE, related_name='ratings'
    )
    rated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ratings_given'
    )
    rating = models.PositiveIntegerField(
        help_text='Rating from 1 to 5'
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('donor', 'rated_by')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rated_by} rated {self.donor} — {self.rating}/5'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update donor's average rating
        ratings = self.donor.ratings.all()
        avg = ratings.aggregate(models.Avg('rating'))['rating__avg'] or 5.0
        self.donor.rating = round(avg, 2)
        self.donor.total_ratings = ratings.count()
        self.donor.save(update_fields=['rating', 'total_ratings'])


class FavoriteHospital(models.Model):
    """Donors can save their favorite hospitals for quick access."""
    donor = models.ForeignKey(
        DonorProfile, on_delete=models.CASCADE, related_name='favorite_hospitals'
    )
    hospital = models.ForeignKey(
        'hospitals.HospitalProfile', on_delete=models.CASCADE, related_name='favorited_by'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('donor', 'hospital')

    def __str__(self):
        return f'{self.donor} ♥ {self.hospital}'
