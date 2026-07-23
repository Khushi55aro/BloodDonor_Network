from django.contrib import admin
from .models import HospitalProfile

@admin.register(HospitalProfile)
class HospitalProfileAdmin(admin.ModelAdmin):
    list_display = ('hospital_name', 'hospital_type', 'user', 'is_verified', 'has_blood_bank', 'total_beds')
    list_filter = ('hospital_type', 'is_verified', 'has_blood_bank')
    search_fields = ('hospital_name', 'registration_number', 'user__city')
