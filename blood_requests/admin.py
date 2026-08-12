from django.contrib import admin
from .models import BloodRequest, RequestResponse


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('requester', 'blood_group', 'units_required', 'status', 'is_emergency', 'created_at')
    list_filter = ('blood_group', 'status', 'is_emergency')
    search_fields = ('requester__username', 'address')


@admin.register(RequestResponse)
class RequestResponseAdmin(admin.ModelAdmin):
    list_display = ('request', 'donor', 'status', 'created_at')
    list_filter = ('status',)
