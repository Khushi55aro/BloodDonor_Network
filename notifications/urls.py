from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notification_list_view, name='list'),
    path('read/<int:notification_id>/', views.mark_as_read_view, name='mark_read'),
    path('api/unread-count/', views.api_unread_count, name='api_unread_count'),
    path('api/latest/', views.api_latest_notifications, name='api_latest'),
]
