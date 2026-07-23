from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_router_view, name='index'),
    path('admin-panel/', views.admin_dashboard_view, name='admin_dashboard'),
]
