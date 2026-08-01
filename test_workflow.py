"""
Full end-to-end integration test script for Blood Donor Network workflow.
Run with: python test_workflow.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donor_network.settings')

from django.conf import settings
settings.ALLOWED_HOSTS = ['*']

django.setup()

from django.test import Client
from django.utils import timezone
from accounts.models import User
from donors.models import DonorProfile
from recipients.models import RecipientProfile
from blood_requests.models import BloodRequest, RequestResponse
from notifications.models import Notification
from reports.models import DonationRecord

client = Client()
errors = []
passed = []

def check(label, condition):
    if condition:
        passed.append(label)
        print(f"  PASS: {label}")
    else:
        errors.append(label)
        print(f"  FAIL: {label}")

print("\n==========================================")
print("=== BLOOD DONOR NETWORK END-TO-END TEST ===")
print("==========================================")

# Cleanup any previous test data
User.objects.filter(username__in=['donor_wf', 'recip_wf', 'admin_wf']).delete()

# 1. Create Admin
admin = User.objects.create_superuser('admin_wf', 'admin_wf@test.com', 'AdminPass123')
admin.role = User.Role.ADMIN
admin.save()
check("Admin user created", admin is not None)

# 2. Register & Setup Donor
donor_user = User.objects.create_user(
    username='donor_wf', email='donor_wf@test.com', password='DonorPass123',
    first_name='John', last_name='Donor', role=User.Role.DONOR,
    phone='9876543210', latitude=19.0760, longitude=72.8777, city='Mumbai'
)
donor_profile, _ = DonorProfile.objects.get_or_create(user=donor_user)
donor_profile.blood_group = 'O-'  # Universal donor
donor_profile.gender = 'M'
donor_profile.age = 25
donor_profile.weight = 70.0
donor_profile.availability_status = 'available'
donor_profile.save()

check("Donor created with O- blood group", donor_profile.blood_group == 'O-')
check("Donor is eligible to donate", donor_profile.is_eligible is True)

# 3. Register & Setup Recipient
recip_user = User.objects.create_user(
    username='recip_wf', email='recip_wf@test.com', password='RecipPass123',
    first_name='Jane', last_name='Recipient', role=User.Role.RECIPIENT,
    phone='9123456789', latitude=19.0800, longitude=72.8800, city='Mumbai'
)
recip_profile, _ = RecipientProfile.objects.get_or_create(user=recip_user)
check("Recipient user created", recip_profile is not None)

# 4. Login as Recipient & Create Blood Request
client.post('/accounts/login/', {'username': 'recip_wf', 'password': 'RecipPass123'})

req_resp = client.post('/blood-requests/create/', {
    'patient_name': 'Emergency Patient',
    'blood_group': 'A+',
    'units_required': 1,
    'urgency_level': 'critical',
    'required_before': (timezone.now() + timezone.timedelta(days=2)).strftime('%Y-%m-%d'),
    'hospital_name': 'City Emergency Hospital',
    'hospital_address': 'Sector 5, Mumbai',
    'latitude': 19.0800,
    'longitude': 72.8800,
    'notes': 'Urgent requirement for surgery'
})
check("Blood request creation response 302", req_resp.status_code == 302)

blood_req = BloodRequest.objects.filter(requester=recip_user).first()
check("Blood request created in DB", blood_req is not None)
check("Blood request automatically flagged as emergency", blood_req.is_emergency is True)

# 5. Verify Geo-Matching Engine & Notifications
resp_link = RequestResponse.objects.filter(request=blood_req, donor=donor_user).first()
check("Geo-matching found O- universal donor for A+ request", resp_link is not None)
check("Haversine distance calculated (< 5km)", resp_link and resp_link.distance_km < 5.0)

notif = Notification.objects.filter(user=donor_user).first()
check("Notification sent to donor", notif is not None)
check("Notification title contains EMERGENCY", notif and 'EMERGENCY' in notif.title)

client.get('/accounts/logout/')

# 6. Privacy Protection Check (Before Donor Accepts)
client.post('/accounts/login/', {'username': 'recip_wf', 'password': 'RecipPass123'})
detail_page = client.get(f'/blood-requests/{blood_req.id}/')
check("Detail page loads for requester (200)", detail_page.status_code == 200)
check("Donor phone number hidden before acceptance", b'Hidden until donor accepts' in detail_page.content)
client.get('/accounts/logout/')

# 7. Donor Accepts Request
client.post('/accounts/login/', {'username': 'donor_wf', 'password': 'DonorPass123'})
accept_resp = client.post(f'/blood-requests/{blood_req.id}/respond/', {'action': 'accept'})
check("Donor accept response 302", accept_resp.status_code == 302)

resp_link.refresh_from_db()
check("RequestResponse status changed to accepted", resp_link.status == 'accepted')

# Verify Donor sees Requester Phone Number after acceptance
donor_detail = client.get(f'/blood-requests/{blood_req.id}/')
check("Requester phone number visible to accepted donor", b'9123456789' in donor_detail.content)

client.get('/accounts/logout/')

# 8. Privacy Protection Check (After Donor Accepts - Requester view)
client.post('/accounts/login/', {'username': 'recip_wf', 'password': 'RecipPass123'})
detail_after_accept = client.get(f'/blood-requests/{blood_req.id}/')
check("Donor phone number NOW visible to requester", b'9876543210' in detail_after_accept.content)

# 9. Complete Donation Workflow
complete_resp = client.post(f'/blood-requests/{blood_req.id}/complete/')
check("Complete donation response 302", complete_resp.status_code == 302)

blood_req.refresh_from_db()
check("Blood request status is fulfilled", blood_req.status == 'fulfilled')
check("Units fulfilled updated to 1", blood_req.units_fulfilled == 1)

donor_profile.refresh_from_db()
check("Donor total donations incremented to 1", donor_profile.total_donations == 1)
check("Donor last donation date updated to today", donor_profile.last_donation_date == timezone.now().date())

cert_record = DonationRecord.objects.filter(donor=donor_user).first()
check("DonationRecord certificate created", cert_record is not None)
check("Certificate ID starts with CERT-", cert_record and cert_record.certificate_id.startswith('CERT-'))

# 10. PDF Certificate Download
pdf_resp = client.get(f'/reports/certificate/{cert_record.id}/')
check("PDF certificate generation returns 200", pdf_resp.status_code == 200)
check("PDF content type is application/pdf", pdf_resp.headers.get('Content-Type') == 'application/pdf')

# 11. Admin Panel User Management
client.get('/accounts/logout/')
client.post('/accounts/login/', {'username': 'admin_wf', 'password': 'AdminPass123'})

admin_users_page = client.get('/dashboard/admin-panel/users/')
check("Admin user management page loads (200)", admin_users_page.status_code == 200)
check("Contains donor_wf in management list", b'donor_wf' in admin_users_page.content)

toggle_status_resp = client.get(f'/dashboard/admin-panel/users/{donor_user.id}/toggle-status/')
check("Admin toggle status redirects 302", toggle_status_resp.status_code == 302)

donor_user.refresh_from_db()
check("Donor user is now deactivated", donor_user.is_active is False)

# Cleanup
User.objects.filter(username__in=['donor_wf', 'recip_wf', 'admin_wf']).delete()

print(f"\n{'='*50}")
print(f"Results: {len(passed)} passed, {len(errors)} failed")
if errors:
    print("FAILURES:")
    for e in errors:
        print(f"  - {e}")
else:
    print("ALL WORKFLOW TESTS PASSED PERFECTLY!")
print()
