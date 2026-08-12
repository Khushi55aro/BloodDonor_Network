"""
Notification model for Blood Donor Network.
"""

from django.db import models
from django.conf import settings


class Notification(models.Model):
    """
    Simple in-app notification model.
    """

    TYPE_CHOICES = [
        ('emergency', 'Emergency Request'),
        ('new_request', 'New Blood Request'),
        ('request_accepted', 'Request Accepted'),
        ('general', 'General Notification'),
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
    url = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        status = 'Read' if self.is_read else 'Unread'
        return f'[{status}] {self.title} -> {self.user.username}'
