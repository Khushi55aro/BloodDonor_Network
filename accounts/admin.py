"""
Admin configuration for custom User model.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'city', 'is_active')
    list_filter = ('role', 'is_active', 'city')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'city')
    ordering = ('-date_joined',)

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Contact', {
            'fields': ('role', 'phone')
        }),
        ('Location', {
            'fields': ('address', 'city', 'latitude', 'longitude')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Role', {
            'fields': ('role', 'email')
        }),
    )
