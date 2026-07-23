"""
Core models — site-wide content like FAQ, Testimonials, Contact Messages.
"""

from django.db import models


class ContactMessage(models.Model):
    """Messages submitted via the public contact form."""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} — {self.name}'


class FAQ(models.Model):
    """Frequently Asked Questions for the platform."""
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    """User testimonials displayed on the home page."""
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, help_text='e.g. Donor, Recipient, Hospital Staff')
    message = models.TextField()
    photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    rating = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.role}'


class SuccessStory(models.Model):
    """Success stories of lives saved through the platform."""
    title = models.CharField(max_length=200)
    story = models.TextField()
    image = models.ImageField(upload_to='success_stories/', blank=True, null=True)
    donor_name = models.CharField(max_length=100, blank=True)
    recipient_name = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Success Stories'

    def __str__(self):
        return self.title
