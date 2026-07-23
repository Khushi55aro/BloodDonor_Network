"""
Notification model for the Blood Donor Network.
Supports multiple notification types and AJAX-based real-time polling.
"""

from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    In-app notification for users. Polled via AJAX for real-time updates.
    """

    TYPE_CHOICES = [
        ('emergency', 'Emergency Request'),
        ('request_accepted', 'Donation Accepted'),
        ('request_rejected', 'Donation Rejected'),
        ('donation_completed', 'Donation Completed'),
        ('eligibility_update', 'Eligibility Updated'),
        ('new_request', 'New Blood Request'),
        ('admin_announcement', 'Admin Announcement'),
        ('profile_verified', 'Profile Verified'),
        ('rating_received', 'Rating Received'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=30, choices=TYPE_CHOICES, default='general'
    )
    is_read = models.BooleanField(default=False)
    url = models.CharField(
        max_length=500, blank=True, null=True,
        help_text='Link to navigate to when notification is clicked.'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        status = '✓' if self.is_read else '●'
        return f'{status} {self.title} → {self.user.username}'
