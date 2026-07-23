from django.urls import path
from . import views

app_name = 'recipients'

urlpatterns = [
    path('dashboard/', views.recipient_dashboard_view, name='dashboard'),
    path('profile/edit/', views.recipient_profile_edit_view, name='profile_edit'),
]
