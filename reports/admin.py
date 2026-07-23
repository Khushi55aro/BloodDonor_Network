from django.contrib import admin
from .models import DonationRecord

@admin.register(DonationRecord)
class DonationRecordAdmin(admin.ModelAdmin):
    list_display = ('donor', 'blood_group', 'units_donated', 'hospital_name', 'donation_date', 'is_verified', 'certificate_id')
    list_filter = ('blood_group', 'is_verified', 'donation_date')
    search_fields = ('donor__username', 'donor__first_name', 'hospital_name', 'certificate_id')
    readonly_fields = ('certificate_id',)
