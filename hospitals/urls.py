from django.urls import path
from . import views

app_name = 'hospitals'

urlpatterns = [
    path('portal/', views.hospital_portal_view, name='portal'),
    path('profile/edit/', views.hospital_profile_edit_view, name='profile_edit'),
]
