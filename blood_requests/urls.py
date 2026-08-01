from django.urls import path
from . import views

app_name = 'blood_requests'

urlpatterns = [
    path('', views.request_list_view, name='list'),
    path('create/', views.create_blood_request_view, name='create'),
    path('<int:request_id>/', views.request_detail_view, name='request_detail'),
    path('<int:request_id>/respond/', views.respond_to_request_view, name='respond'),
    path('<int:request_id>/complete/', views.complete_blood_request_view, name='complete'),
    path('<int:request_id>/cancel/', views.cancel_blood_request_view, name='cancel'),
]
