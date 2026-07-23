from django.contrib import admin
from .models import RecipientProfile

@admin.register(RecipientProfile)
class RecipientProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_group_needed', 'total_requests', 'total_fulfilled')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
