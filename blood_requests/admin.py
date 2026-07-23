from django.contrib import admin
from .models import BloodRequest, RequestResponse

@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('patient_name', 'blood_group', 'urgency_level', 'units_required', 'units_fulfilled', 'status', 'is_emergency', 'required_before', 'created_at')
    list_filter = ('blood_group', 'urgency_level', 'status', 'is_emergency')
    search_fields = ('patient_name', 'hospital_name', 'requester__username')
    readonly_fields = ('units_fulfilled',)

@admin.register(RequestResponse)
class RequestResponseAdmin(admin.ModelAdmin):
    list_display = ('request', 'donor', 'status', 'distance_km', 'responded_at')
    list_filter = ('status',)
