from django.urls import path
from . import views

app_name = 'donors'

urlpatterns = [
    path('dashboard/', views.donor_dashboard_view, name='dashboard'),
    path('profile/edit/', views.donor_profile_edit_view, name='profile_edit'),
    path('toggle-availability/', views.toggle_availability_view, name='toggle_availability'),
]
