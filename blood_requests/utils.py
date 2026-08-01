"""
Utility functions for blood donor matching and compatibility.
"""

from donors.models import DonorProfile
from blood_requests.models import RequestResponse
from notifications.models import Notification

# Blood Group Compatibility Matrix
# Key: Recipient Blood Group, Value: List of Compatible Donor Blood Groups
BLOOD_COMPATIBILITY = {
    'A+': ['A+', 'A-', 'O+', 'O-'],
    'A-': ['A-', 'O-'],
    'B+': ['B+', 'B-', 'O+', 'O-'],
    'B-': ['B-', 'O-'],
    'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],  # Universal recipient
    'AB-': ['AB-', 'A-', 'B-', 'O-'],
    'O+': ['O+', 'O-'],
    'O-': ['O-'],  # Universal donor
}


def find_and_notify_eligible_donors(blood_request, radius_km=50):
    """
    Finds all eligible donors near the blood request location matching compatible blood groups.
    Calculates Haversine distance, creates RequestResponse objects, and sends notifications.
    Returns the count of donors notified.
    """
    if not blood_request.latitude or not blood_request.longitude:
        return 0

    compatible_groups = BLOOD_COMPATIBILITY.get(blood_request.blood_group, [blood_request.blood_group])
    
    # Filter potential donors
    potential_donors = DonorProfile.objects.select_related('user').filter(
        blood_group__in=compatible_groups
    ).exclude(availability_status='unavailable')

    matched_donors = []

    for donor in potential_donors:
        # Check eligibility (cooldown, age, weight, etc.)
        if not donor.is_eligible:
            continue

        if not donor.user.latitude or not donor.user.longitude:
            continue

        distance = donor.distance_to(blood_request.latitude, blood_request.longitude)
        
        # Increase radius to 100km for emergency requests
        max_dist = 100 if blood_request.is_emergency else radius_km

        if distance is not None and distance <= max_dist:
            matched_donors.append((donor, distance))

    # Sort matched donors nearest first
    matched_donors.sort(key=lambda x: x[1])

    notified_count = 0
    for donor, distance in matched_donors:
        # Create or update RequestResponse
        resp, created = RequestResponse.objects.get_or_create(
            request=blood_request,
            donor=donor.user,
            defaults={'distance_km': round(distance, 2), 'status': 'pending'}
        )
        if not created and resp.distance_km != round(distance, 2):
            resp.distance_km = round(distance, 2)
            resp.save(update_fields=['distance_km'])

        # Create Notification if newly matched
        notification_type = 'emergency' if blood_request.is_emergency else 'new_request'
        title = 'EMERGENCY Blood Request' if blood_request.is_emergency else 'New Blood Request'
        
        Notification.objects.get_or_create(
            user=donor.user,
            notification_type=notification_type,
            url=f"/blood-requests/{blood_request.id}/",
            defaults={
                'title': f"{title}: {blood_request.blood_group} near you!",
                'message': f"A patient needs {blood_request.units_required} unit(s) of {blood_request.blood_group} blood at {blood_request.hospital_name} ({round(distance, 1)} km away)."
            }
        )
        notified_count += 1

    return notified_count
