from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('dashboard/', views.reports_dashboard_view, name='dashboard'),
    path('export/csv/', views.export_donations_csv, name='export_csv'),
    path('certificate/<int:record_id>/', views.download_certificate_pdf, name='download_certificate'),
]
