from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_router_view, name='index'),
    path('admin-panel/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/users/', views.admin_manage_users_view, name='admin_manage_users'),
    path('admin-panel/users/<int:user_id>/toggle-status/', views.admin_toggle_user_status_view, name='admin_toggle_user_status'),
    path('admin-panel/users/<int:user_id>/delete/', views.admin_delete_user_view, name='admin_delete_user'),
    path('admin-panel/verify/<str:entity_type>/<int:entity_id>/', views.admin_toggle_verification_view, name='admin_toggle_verification'),
]
