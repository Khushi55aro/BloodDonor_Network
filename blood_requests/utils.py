"""
Utility functions for Blood-Group Compatibility, Haversine Distance, and Geo-Matching algorithm.
"""

import math
from donors.models import DonorProfile
from blood_requests.models import RequestResponse
from notifications.models import Notification


# Standard Blood Group Compatibility Dictionary
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


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula. Returns distance in kilometers.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None

    R = 6371.0  # Earth's radius in kilometers

    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(
        math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)]
    )

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2.0) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.asin(math.sqrt(a))

    return R * c


def find_and_notify_eligible_donors(blood_request, radius_km=30):
    """
    Geo-Matching Algorithm:
    1. Find compatible donor blood groups using BLOOD_COMPATIBILITY dictionary.
    2. Check donor eligibility (90-day cooldown check).
    3. Check donor availability.
    4. Check donor has valid latitude and longitude coordinates.
    5. Calculate Haversine distance from donor to blood request location.
    6. Filter donors within radius_km (default 30 km).
    7. Sort donors by distance (nearest donors first).
    8. Create RequestResponse and send in-app Notification to matched donors.
    """
    if blood_request.latitude is None or blood_request.longitude is None:
        return 0

    # 1. Get compatible blood groups
    compatible_groups = BLOOD_COMPATIBILITY.get(
        blood_request.blood_group, [blood_request.blood_group]
    )

    # 2. Query potential donors with compatible blood group
    potential_donors = DonorProfile.objects.select_related('user').filter(
        blood_group__in=compatible_groups
    )

    matched_donors = []

    for donor in potential_donors:
        # 3. Check donor eligibility (cooldown + availability)
        if not donor.is_eligible:
            continue

        # 4. Check donor coordinates
        if donor.user.latitude is None or donor.user.longitude is None:
            continue

        # 5. Calculate Haversine distance
        dist = haversine_distance(
            donor.user.latitude, donor.user.longitude,
            blood_request.latitude, blood_request.longitude
        )

        # 6. Check within radius
        if dist is not None and dist <= radius_km:
            matched_donors.append((donor, dist))

    # 7. Sort nearest first
    matched_donors.sort(key=lambda item: item[1])

    # 8. Create RequestResponse and Notification records
    notified_count = 0
    for donor, dist in matched_donors:
        # Create response record if it doesn't exist
        RequestResponse.objects.get_or_create(
            request=blood_request,
            donor=donor.user,
            defaults={'status': 'Pending'}
        )

        # Create notification
        notif_type = 'emergency' if blood_request.is_emergency else 'new_request'
        prefix = "EMERGENCY: " if blood_request.is_emergency else ""
        
        Notification.objects.get_or_create(
            user=donor.user,
            notification_type=notif_type,
            url=f"/blood-requests/{blood_request.id}/",
            defaults={
                'title': f"{prefix}Matching Blood Request for {blood_request.blood_group}",
                'message': f"A blood request for {blood_group_needed_text(blood_request)} is available near your location ({round(dist, 1)} km away)."
            }
        )
        notified_count += 1

    return notified_count


def blood_group_needed_text(blood_request):
    return f"{blood_request.units_required} unit(s) of {blood_request.blood_group}"
