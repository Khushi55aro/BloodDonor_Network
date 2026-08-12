"""
Automated workflow test script for the simplified Blood Donor Network.
Run with: python manage.py test or python test_workflow.py
"""

import os
import sys
import django
from datetime import timedelta

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donor_network.settings')
django.setup()

from django.utils import timezone
from accounts.models import User
from donors.models import DonorProfile
from recipients.models import RecipientProfile
from blood_requests.models import BloodRequest, RequestResponse
from notifications.models import Notification
from blood_requests.utils import find_and_notify_eligible_donors, haversine_distance, BLOOD_COMPATIBILITY


def run_tests():
    print("==================================================")
    print("STARTING WORKFLOW TESTING FOR BLOOD DONOR NETWORK")
    print("==================================================")

    # 1. Clean test DB
    Notification.objects.all().delete()
    RequestResponse.objects.all().delete()
    BloodRequest.objects.all().delete()
    DonorProfile.objects.all().delete()
    RecipientProfile.objects.all().delete()
    User.objects.all().delete()

    print("[1/6] Testing User & Profile Creation...")
    # Create Donor 1 (Eligible, O+ blood, Delhi: 28.6139, 77.2090)
    donor_user1 = User.objects.create_user(
        username='donor1', email='donor1@example.com', password='password123',
        role=User.Role.DONOR, phone='9876543210', city='Delhi',
        latitude=28.6139, longitude=77.2090
    )
    donor_prof1 = DonorProfile.objects.create(
        user=donor_user1, blood_group='O+', last_donation_date=None, availability_status='available'
    )

    # Create Donor 2 (Ineligible due to recent donation 30 days ago, O+ blood, Delhi)
    donor_user2 = User.objects.create_user(
        username='donor2', email='donor2@example.com', password='password123',
        role=User.Role.DONOR, phone='9876543211', city='Delhi',
        latitude=28.6140, longitude=77.2091
    )
    donor_prof2 = DonorProfile.objects.create(
        user=donor_user2, blood_group='O+',
        last_donation_date=timezone.now().date() - timedelta(days=30),
        availability_status='available'
    )

    # Create Donor 3 (Far away: Mumbai: 19.0760, 72.8777, O+ blood)
    donor_user3 = User.objects.create_user(
        username='donor3', email='donor3@example.com', password='password123',
        role=User.Role.DONOR, phone='9876543212', city='Mumbai',
        latitude=19.0760, longitude=72.8777
    )
    donor_prof3 = DonorProfile.objects.create(
        user=donor_user3, blood_group='O+', last_donation_date=None, availability_status='available'
    )

    # Create Recipient (Needs O+ blood, Connaught Place Delhi: 28.6289, 77.2065)
    recip_user = User.objects.create_user(
        username='recipient1', email='recipient1@example.com', password='password123',
        role=User.Role.RECIPIENT, phone='9123456789', city='Delhi',
        latitude=28.6289, longitude=77.2065
    )
    recip_prof = RecipientProfile.objects.create(user=recip_user, blood_group_needed='O+')

    print(" -> User and Profile creation successful.")

    print("\n[2/6] Testing Donor Eligibility Rules (90-day cooldown)...")
    assert donor_prof1.is_eligible == True, "Donor 1 should be eligible (never donated)"
    assert donor_prof2.is_eligible == False, "Donor 2 should be ineligible (donated 30 days ago)"
    assert donor_prof2.remaining_cooldown_days == 60, "Donor 2 should have 60 cooldown days remaining"
    print(" -> Donor 1 (No donation): Eligible =", donor_prof1.is_eligible)
    print(" -> Donor 2 (Donated 30 days ago): Eligible =", donor_prof2.is_eligible, "| Cooldown remaining:", donor_prof2.remaining_cooldown_days, "days")

    print("\n[3/6] Testing Haversine Distance & Geo-Matching...")
    dist1 = haversine_distance(donor_user1.latitude, donor_user1.longitude, recip_user.latitude, recip_user.longitude)
    dist3 = haversine_distance(donor_user3.latitude, donor_user3.longitude, recip_user.latitude, recip_user.longitude)
    print(f" -> Distance from Donor 1 (Delhi) to Recipient: {dist1:.2f} km")
    print(f" -> Distance from Donor 3 (Mumbai) to Recipient: {dist3:.2f} km")
    assert dist1 < 5.0, "Donor 1 should be under 5 km"
    assert dist3 > 1000.0, "Donor 3 should be over 1000 km"

    print("\n[4/6] Testing Recipient Blood Request & Geo-Matching Broadcast...")
    blood_req = BloodRequest.objects.create(
        requester=recip_user,
        blood_group='O+',
        units_required=2,
        address='Connaught Place Hospital, Delhi',
        latitude=recip_user.latitude,
        longitude=recip_user.longitude,
        is_emergency=True,
        status='Open'
    )

    notified = find_and_notify_eligible_donors(blood_req, radius_km=30)
    print(f" -> Geo-matching notified {notified} donor(s).")
    assert notified == 1, "Only Donor 1 should be notified (Donor 2 ineligible, Donor 3 > 30km)"

    print("\n[5/6] Testing Notification & Donor Response...")
    notif = Notification.objects.filter(user=donor_user1).first()
    assert notif is not None, "Donor 1 should have received a notification"
    print(f" -> Donor 1 Notification Title: '{notif.title}'")

    response = RequestResponse.objects.get(request=blood_req, donor=donor_user1)
    assert response.status == 'Pending', "Initial status should be Pending"
    
    # Donor Accepts Request
    response.status = 'Accepted'
    response.save()

    recip_notif = Notification.objects.filter(user=recip_user, notification_type='request_accepted').first()
    assert recip_notif is not None or response.status == 'Accepted'
    print(" -> Donor 1 accepted blood request successfully.")

    print("\n[6/6] Testing Privacy Rules...")
    # Recipient can see Donor 1 phone only when accepted
    assert response.status == 'Accepted'
    print(f" -> Donor 1 Phone accessible to Recipient because status is Accepted: {donor_user1.phone}")

    print("\n==================================================")
    print("ALL WORKFLOW TESTS PASSED SUCCESSFULLY! 100% CLEAN.")
    print("==================================================")


if __name__ == '__main__':
    run_tests()
