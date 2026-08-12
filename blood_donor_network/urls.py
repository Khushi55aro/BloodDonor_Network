"""
Main URL Configuration for Blood Donor Network.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('donors/', include('donors.urls')),
    path('recipients/', include('recipients.urls')),
    path('blood-requests/', include('blood_requests.urls')),
    path('notifications/', include('notifications.urls')),
]
