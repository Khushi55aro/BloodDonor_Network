import os
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from accounts.models import User
from donors.models import DonorProfile
from recipients.models import RecipientProfile
from hospitals.models import HospitalProfile
from blood_requests.models import BloodRequest
from core.models import FAQ, Testimonial


class Command(BaseCommand):
    help = 'Populates the database with dummy data for testing.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating database...')

        # 1. Create Superuser / Admin
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser('admin', 'admin@bloodnet.com', 'admin123')
            admin.role = User.Role.ADMIN
            admin.save()
            self.stdout.write(self.style.SUCCESS('Created Admin user (admin / admin123)'))

        # 2. Create Donors
        blood_groups = ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
        cities = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad']
        
        for i in range(1, 6):
            username = f'donor{i}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'donor{i}@example.com',
                    password='password123',
                    first_name=f'John{i}',
                    last_name='Doe',
                    role=User.Role.DONOR,
                    city=random.choice(cities),
                    latitude=19.0760 + random.uniform(-0.1, 0.1),
                    longitude=72.8777 + random.uniform(-0.1, 0.1)
                )
                
                # Create Donor Profile
                bg = random.choice(blood_groups)
                DonorProfile.objects.create(
                    user=user,
                    blood_group=bg,
                    gender=random.choice(['M', 'F']),
                    age=random.randint(20, 45),
                    weight=random.randint(60, 90),
                    total_donations=random.randint(0, 5),
                    last_donation_date=timezone.now().date() - timedelta(days=random.randint(100, 300))
                )
        self.stdout.write(self.style.SUCCESS('Created 5 Mock Donors (donor1-donor5 / password123)'))

        # 3. Create Hospitals
        for i in range(1, 3):
            username = f'hospital{i}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'hospital{i}@example.com',
                    password='password123',
                    first_name=f'City',
                    last_name=f'Hospital {i}',
                    role=User.Role.HOSPITAL,
                    city='Mumbai',
                    latitude=19.0760 + random.uniform(-0.05, 0.05),
                    longitude=72.8777 + random.uniform(-0.05, 0.05)
                )
                
                HospitalProfile.objects.create(
                    user=user,
                    hospital_name=f'City Central Hospital {i}',
                    registration_number=f'REG-{1000+i}',
                    hospital_type='private',
                    total_beds=250,
                    has_blood_bank=True,
                    is_verified=True
                )
        self.stdout.write(self.style.SUCCESS('Created 2 Mock Hospitals (hospital1-hospital2 / password123)'))

        # 4. Create Recipients and Blood Requests
        for i in range(1, 3):
            username = f'recipient{i}'
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f'recipient{i}@example.com',
                    password='password123',
                    first_name=f'Jane{i}',
                    last_name='Smith',
                    role=User.Role.RECIPIENT,
                    city='Mumbai'
                )
                RecipientProfile.objects.create(user=user)
                
                # Create Request
                BloodRequest.objects.create(
                    requester=user,
                    blood_group=random.choice(blood_groups),
                    patient_name=f'Relative of Jane{i}',
                    hospital_name='City Central Hospital 1',
                    hospital_address='123 Main St, Mumbai',
                    units_required=random.randint(1, 3),
                    urgency_level='urgent',
                    required_before=timezone.now().date() + timedelta(days=random.randint(1, 5)),
                    latitude=19.0760,
                    longitude=72.8777
                )
        self.stdout.write(self.style.SUCCESS('Created 2 Mock Recipients and Requests (recipient1-recipient2 / password123)'))

        # 5. Create Core Data
        if not FAQ.objects.exists():
            FAQ.objects.create(question='Who can donate blood?', answer='Generally, anyone between 18 and 65 years old weighing at least 50 kg and in good health can donate blood.', order=1)
            FAQ.objects.create(question='How often can I donate?', answer='Men can donate every 90 days, and women every 120 days.', order=2)
            
        if not Testimonial.objects.exists():
            Testimonial.objects.create(name='Sarah Johnson', role='Donor', message='Donating through BloodNet was so easy and I felt great knowing I helped someone nearby.', rating=5)

        self.stdout.write(self.style.SUCCESS('Successfully populated database with mock data!'))
