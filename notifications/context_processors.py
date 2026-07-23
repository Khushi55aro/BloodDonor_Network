"""
Notification context processor — injects unread notification count
into every template context for the navbar badge.
"""


def unread_notifications_count(request):
    """Add unread_notifications_count to template context for authenticated users."""
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}
