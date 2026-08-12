from django.contrib import admin
from .models import DonorProfile


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_group', 'last_donation_date', 'availability_status', 'is_eligible')
    list_filter = ('blood_group', 'availability_status')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__city')
