"""
Smoke test script for registration & authentication module.
Run with: python test_auth.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blood_donor_network.settings')

# Must set ALLOWED_HOSTS before django.setup() for the test client
from django.conf import settings
settings.ALLOWED_HOSTS = ['*']

django.setup()

from django.test import Client
from accounts.models import User
from donors.models import DonorProfile
from recipients.models import RecipientProfile
from hospitals.models import HospitalProfile

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

print("\n=== 1. Choose Role Page ===")
resp = client.get('/accounts/register/')
check("Choose role page returns 200", resp.status_code == 200)
check("Has Donor card", b'Register as Donor' in resp.content)
check("Has Recipient card", b'Register as Recipient' in resp.content)
check("Has Hospital card", b'Register as Hospital' in resp.content)

print("\n=== 2. Donor Registration ===")
resp = client.get('/accounts/register/donor/')
check("Donor register page returns 200", resp.status_code == 200)

resp = client.post('/accounts/register/donor/', {
    'first_name': 'Donor', 'last_name': 'Test',
    'username': 'donortest1', 'email': 'donor@test.com',
    'phone': '9999999999',
    'password1': 'StrongPass@123', 'password2': 'StrongPass@123',
})
check("Donor registration redirects (302)", resp.status_code == 302)
check("Redirects to login page", resp.status_code == 302 and '/accounts/login/' in resp.url)

user = User.objects.filter(username='donortest1').first()
check("Donor user created", user is not None)
check("User role is DONOR", user and user.role == 'DONOR')
check("DonorProfile created", user and DonorProfile.objects.filter(user=user).exists())
donor_profile = DonorProfile.objects.filter(user=user).first()
check("blood_group is empty (no fake default)", donor_profile and donor_profile.blood_group is None)
check("age is empty (no fake default)", donor_profile and donor_profile.age is None)
check("weight is empty (no fake default)", donor_profile and donor_profile.weight is None)
check("NOT auto-logged-in after registration", '_auth_user_id' not in client.session)

print("\n=== 3. Recipient Registration ===")
resp = client.post('/accounts/register/recipient/', {
    'first_name': 'Recip', 'last_name': 'Test',
    'username': 'reciptest1', 'email': 'recip@test.com',
    'phone': '8888888888',
    'password1': 'StrongPass@123', 'password2': 'StrongPass@123',
})
check("Recipient registration redirects (302)", resp.status_code == 302)
check("Redirects to login page", resp.status_code == 302 and '/accounts/login/' in resp.url)
user_r = User.objects.filter(username='reciptest1').first()
check("Recipient user created", user_r is not None)
check("User role is RECIPIENT", user_r and user_r.role == 'RECIPIENT')
check("RecipientProfile created", user_r and RecipientProfile.objects.filter(user=user_r).exists())

print("\n=== 4. Hospital Registration ===")
resp = client.post('/accounts/register/hospital/', {
    'first_name': 'Hosp', 'last_name': 'Admin',
    'username': 'hosptest1', 'email': 'hosp@test.com',
    'phone': '7777777777',
    'hospital_name': 'City Blood Bank',
    'password1': 'StrongPass@123', 'password2': 'StrongPass@123',
})
check("Hospital registration redirects (302)", resp.status_code == 302)
check("Redirects to login page", resp.status_code == 302 and '/accounts/login/' in resp.url)
user_h = User.objects.filter(username='hosptest1').first()
check("Hospital user created", user_h is not None)
check("User role is HOSPITAL", user_h and user_h.role == 'HOSPITAL')
hp = HospitalProfile.objects.filter(user=user_h).first()
check("HospitalProfile created", hp is not None)
check("Hospital name is from form", hp and hp.hospital_name == 'City Blood Bank')

print("\n=== 5. Login & Dashboard Redirect ===")
# Donor login
resp = client.post('/accounts/login/', {'username': 'donortest1', 'password': 'StrongPass@123'})
check("Donor login redirects (302)", resp.status_code == 302)
check("Donor -> dashboard router", resp.status_code == 302 and 'dashboard' in resp.url)

resp2 = client.get('/dashboard/')
check("Dashboard router -> donors/dashboard", resp2.status_code == 302 and 'donors' in resp2.url)
client.get('/accounts/logout/')

# Recipient login
resp = client.post('/accounts/login/', {'username': 'reciptest1', 'password': 'StrongPass@123'})
check("Recipient login redirects (302)", resp.status_code == 302)
resp2 = client.get('/dashboard/')
check("Dashboard router -> recipients/dashboard", resp2.status_code == 302 and 'recipients' in resp2.url)
client.get('/accounts/logout/')

# Hospital login
resp = client.post('/accounts/login/', {'username': 'hosptest1', 'password': 'StrongPass@123'})
check("Hospital login redirects (302)", resp.status_code == 302)
resp2 = client.get('/dashboard/')
check("Dashboard router -> hospitals/portal", resp2.status_code == 302 and 'hospitals' in resp2.url)
client.get('/accounts/logout/')

print("\n=== 6. Role-Based Authorization ===")
# Donor logged in trying to access recipient dashboard
client.post('/accounts/login/', {'username': 'donortest1', 'password': 'StrongPass@123'})
resp = client.get('/recipients/dashboard/')
check("Donor cannot access recipient dashboard (redirected)", resp.status_code == 302)
resp = client.get('/hospitals/portal/')
check("Donor cannot access hospital portal (redirected)", resp.status_code == 302)
client.get('/accounts/logout/')

# Recipient logged in trying to access donor dashboard
client.post('/accounts/login/', {'username': 'reciptest1', 'password': 'StrongPass@123'})
resp = client.get('/donors/dashboard/')
check("Recipient cannot access donor dashboard (redirected)", resp.status_code == 302)
client.get('/accounts/logout/')

print("\n=== 7. Unauthenticated Access ===")
resp = client.get('/donors/dashboard/')
check("Anon cannot access donor dashboard (redirected to login)", resp.status_code == 302 and 'login' in resp.url)
resp = client.get('/recipients/dashboard/')
check("Anon cannot access recipient dashboard (redirected to login)", resp.status_code == 302 and 'login' in resp.url)
resp = client.get('/hospitals/portal/')
check("Anon cannot access hospital portal (redirected to login)", resp.status_code == 302 and 'login' in resp.url)

print("\n=== 8. Logout ===")
client.post('/accounts/login/', {'username': 'donortest1', 'password': 'StrongPass@123'})
resp = client.get('/accounts/logout/')
check("Logout redirects", resp.status_code == 302)
resp = client.get('/donors/dashboard/')
check("After logout, cannot access dashboard", resp.status_code == 302 and 'login' in resp.url)

# Cleanup
User.objects.filter(username__in=['donortest1', 'reciptest1', 'hosptest1']).delete()

print(f"\n{'='*50}")
print(f"Results: {len(passed)} passed, {len(errors)} failed")
if errors:
    print("FAILURES:")
    for e in errors:
        print(f"  - {e}")
else:
    print("ALL TESTS PASSED!")
print()
