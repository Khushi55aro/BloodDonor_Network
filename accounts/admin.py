"""Admin configuration for the accounts app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_email_verified', 'city', 'is_active')
    list_filter = ('role', 'is_email_verified', 'is_active', 'city', 'state')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'city')
    ordering = ('-date_joined',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Contact', {
            'fields': ('role', 'phone', 'profile_photo', 'date_of_birth')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'pincode', 'latitude', 'longitude')
        }),
        ('Verification', {
            'fields': ('is_email_verified', 'email_verification_token')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role', {
            'fields': ('role', 'email')
        }),
    )
