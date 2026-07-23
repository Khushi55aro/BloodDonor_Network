from django.contrib import admin
from .models import DonorProfile, DonorRating, FavoriteHospital

@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'blood_group', 'gender', 'age', 'weight', 'availability_status', 'is_eligible', 'is_verified', 'total_donations', 'donor_id')
    list_filter = ('blood_group', 'gender', 'availability_status', 'is_verified')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'donor_id', 'user__city')
    readonly_fields = ('donor_id', 'total_donations', 'rating', 'total_ratings')

@admin.register(DonorRating)
class DonorRatingAdmin(admin.ModelAdmin):
    list_display = ('donor', 'rated_by', 'rating', 'created_at')

@admin.register(FavoriteHospital)
class FavoriteHospitalAdmin(admin.ModelAdmin):
    list_display = ('donor', 'hospital', 'added_at')
