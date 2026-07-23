"""
Views for handling notifications, including AJAX endpoints for polling.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_list_view(request):
    """View all notifications for the user."""
    notifications = request.user.notifications.all()
    
    # Mark all as read when viewed on this page
    unread = notifications.filter(is_read=False)
    if unread.exists():
        unread.update(is_read=True)
        
    return render(request, 'notifications/list.html', {'notifications': notifications})


@login_required
def mark_as_read_view(request, notification_id):
    """Mark a specific notification as read and redirect to its URL."""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if notification.url:
        return redirect(notification.url)
    return redirect('notifications:list')


@login_required
def api_unread_count(request):
    """AJAX endpoint for getting the unread notification count."""
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def api_latest_notifications(request):
    """AJAX endpoint for fetching recent unread notifications."""
    notifications = request.user.notifications.filter(is_read=False)[:5]
    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'type': notif.notification_type,
            'url': notif.url or '#',
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    return JsonResponse({'notifications': data})
