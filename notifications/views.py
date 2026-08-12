"""
Views for viewing notifications and marking them as read.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def notification_list_view(request):
    """List all notifications for the user."""
    notifications = request.user.notifications.all().order_by("-created_at")

    # Mark as read when page is opened
    unread = notifications.filter(is_read=False)
    if unread.exists():
        unread.update(is_read=True)

    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
def mark_as_read_view(request, notification_id):
    """Mark a notification as read and redirect to target URL."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    if notification.url:
        return redirect(notification.url)
    return redirect('notifications:list')
