"""
Views for handling blood requests, matching, response tracking, and workflow management.
"""
from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import BloodRequest, RequestResponse
from .forms import BloodRequestForm, BloodRequestSearchForm
from .utils import find_and_notify_eligible_donors, BLOOD_COMPATIBILITY
from donors.models import DonorProfile
from recipients.models import RecipientProfile
from hospitals.models import HospitalProfile
from notifications.models import Notification
from reports.models import DonationRecord


@login_required
def create_blood_request_view(request):
    """View to create a new blood request and trigger matching/notifications."""
    if not (request.user.is_recipient or request.user.is_hospital or request.user.is_staff):
        messages.error(request, 'Only recipients and hospitals can create blood requests.')
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = BloodRequestForm(request.POST, request.FILES)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.requester = request.user

            # If coordinates are missing, fallback to user profile coordinates
            if not blood_request.latitude or not blood_request.longitude:
                blood_request.latitude = request.user.latitude
                blood_request.longitude = request.user.longitude

            blood_request.save()
            # Prevent duplicate active request for the same patient
            existing_request = BloodRequest.objects.filter(requester=request.user,patient_name=blood_request.patient_name,status__in=["open", "in_progress"]).exclude(id=blood_request.id)

            if existing_request.exists():
                blood_request.delete()
                messages.error(request,"An active request already exists for this patient.")
                return redirect("blood_requests:create")

            # Update stats on recipient or hospital profile
            if request.user.is_recipient:
                rec_prof, _ = RecipientProfile.objects.get_or_create(user=request.user)
                rec_prof.total_requests += 1
                rec_prof.save(update_fields=['total_requests'])
            elif request.user.is_hospital:
                hosp_prof, _ = HospitalProfile.objects.get_or_create(user=request.user, defaults={'hospital_name': request.user.username})
                hosp_prof.total_requests += 1
                hosp_prof.save(update_fields=['total_requests'])

            # Run Geo-matching & Notification broadcast
            notified_count = find_and_notify_eligible_donors(blood_request)

            if notified_count > 0:
                messages.success(request, f'Blood request created successfully. Geo-matching notified {notified_count} eligible nearby donor(s).')
            else:
                messages.warning(request, 'Blood request created successfully. No eligible nearby donors found matching your exact criteria right now.')

            return redirect('blood_requests:request_detail', request_id=blood_request.id)
        else:
            messages.error(request, 'Please correct the errors in the form.')
    else:
        # Pre-fill hospital details if user is hospital
        initial_data = {}
        if request.user.is_hospital:
            hospital_profile = getattr(request.user, 'hospital_profile', None)
            if hospital_profile:
                initial_data = {
                    'hospital_name': hospital_profile.hospital_name,
                    'hospital_address': request.user.address or '',
                    'latitude': request.user.latitude,
                    'longitude': request.user.longitude,
                }
        form = BloodRequestForm(initial=initial_data)

    return render(request, 'blood_requests/create_request.html', {'form': form})


@login_required
def request_list_view(request):
    """
    List and search blood requests.
    Privacy rules enforced:
    - Donors see requests matched to them or nearby active emergency requests matching compatible blood group.
    - Requesters & Hospitals see their own created requests.
    - Admins see all requests.
    """
    form = BloodRequestSearchForm(request.GET)
    user = request.user

    if user.is_staff or user.is_admin:
        base_qs = BloodRequest.objects.all()
    elif user.is_donor:
        # Requests where this donor was notified/matched, or open active emergency requests
        donor_profile = getattr(user, 'donor_profile', None)
        donor_bg = donor_profile.blood_group if donor_profile else None
        
        matched_req_ids = RequestResponse.objects.filter(donor=user).values_list('request_id', flat=True)
        
        if donor_bg:
            # Find which recipient blood groups this donor can donate to
            can_donate_to = [bg for bg, donors in BLOOD_COMPATIBILITY.items() if donor_bg in donors]
            emergency_qs = BloodRequest.objects.filter(
                status__in=['open', 'in_progress'],
                is_emergency=True,
                blood_group__in=can_donate_to
            )
            base_qs = BloodRequest.objects.filter(
                models.Q(id__in=matched_req_ids) | models.Q(id__in=emergency_qs.values_list('id', flat=True))
            )
        else:
            base_qs = BloodRequest.objects.filter(id__in=matched_req_ids)
    else:
        # Recipient or Hospital — show their own requests
        base_qs = BloodRequest.objects.filter(requester=user)

    requests = base_qs.select_related('requester').order_by('-is_emergency', '-created_at')

    if form.is_valid():
        blood_group = form.cleaned_data.get('blood_group')
        urgency = form.cleaned_data.get('urgency')
        city = form.cleaned_data.get('city')

        if blood_group:
            requests = requests.filter(blood_group=blood_group)
        if urgency:
            requests = requests.filter(urgency_level=urgency)
        if city:
            requests = requests.filter(
                models.Q(hospital_address__icontains=city) | models.Q(hospital_name__icontains=city)
            )

    # Calculate distance for donors
    if user.is_donor and user.latitude and user.longitude:
        donor_profile = getattr(user, 'donor_profile', None)
        for req in requests:
            if req.latitude and req.longitude and donor_profile:
                req.distance = round(donor_profile.distance_to(req.latitude, req.longitude), 1)
            else:
                req.distance = None

    context = {
        'form': form,
        'requests': requests,
    }
    return render(request, 'blood_requests/list.html', context)


@login_required
def request_detail_view(request, request_id):
    """
    Detailed view of a blood request.
    Enforces privacy rules:
    - Contact details of donors are visible to requester ONLY if donor status is 'accepted'.
    - Contact details of requester are visible to donor ONLY if donor accepted the request.
    - Requesters see matched eligible donors with distance.
    """
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    user = request.user

    # Authorization Check
    is_owner = (user == blood_request.requester or user.is_staff or user.is_admin)
    is_donor = user.is_donor

    responses = blood_request.responses.all().select_related('donor', 'donor__donor_profile')

    user_response = None
    if is_donor:
        user_response = responses.filter(donor=user).first()

    # Geo matched donors list for the requester
    matched_donors = []
    if is_owner and blood_request.latitude and blood_request.longitude:
        compatible_groups = BLOOD_COMPATIBILITY.get(blood_request.blood_group, [blood_request.blood_group])
        all_donors = DonorProfile.objects.select_related('user').filter(
            blood_group__in=compatible_groups
        ).exclude(availability_status='unavailable')

        resp_map = {resp.donor_id: resp for resp in responses}

        for d in all_donors:
            if not d.user.latitude or not d.user.longitude:
                continue
            dist = d.distance_to(blood_request.latitude, blood_request.longitude)
            if dist is not None and dist <= 30:
                resp = resp_map.get(d.user_id)
                matched_donors.append({
                    'donor_profile': d,
                    'user': d.user,
                    'distance': round(dist, 1),
                    'response': resp,
                    'status': resp.status if resp else 'matched'
                })
        matched_donors.sort(key=lambda x: x['distance'])

    context = {
        'blood_request': blood_request,
        'responses': responses,
        'user_response': user_response,
        'is_owner': is_owner,
        'matched_donors': matched_donors,
    }
    return render(request, 'blood_requests/detail.html', context)


@login_required
def respond_to_request_view(request, request_id):
    """Donor action to accept or reject a request."""
    if not request.user.is_donor:
        messages.error(request, 'Only donors can respond to blood requests.')
        return redirect('dashboard:index')

    blood_request = get_object_or_404(BloodRequest, id=request_id)
    action = request.POST.get('action')

    if not blood_request.is_active:
        messages.error(request, 'This blood request is no longer active.')
        return redirect('blood_requests:request_detail', request_id=request_id)

    if action in ['accept', 'reject']:
        donor_profile = getattr(request.user, 'donor_profile', None)
        distance = None
        if donor_profile and blood_request.latitude and blood_request.longitude:
            distance = donor_profile.distance_to(blood_request.latitude, blood_request.longitude)

        response, created = RequestResponse.objects.get_or_create(
            request=blood_request,
            donor=request.user,
            defaults={'distance_km': round(distance, 2) if distance else None}
        )

        new_status = 'accepted' if action == 'accept' else 'rejected'
        response.status = new_status
        response.save()

        if action == 'accept':
            if blood_request.status == 'open':
                blood_request.status = 'in_progress'
                blood_request.save(update_fields=['status'])

            # Notify requester
            Notification.objects.create(
                user=blood_request.requester,
                title='Donor Accepted Your Request!',
                message=f"Good news! Donor {request.user.get_full_name()} ({request.user.phone or 'Contact available in app'}) accepted your blood request for {blood_request.blood_group}.",
                notification_type='request_accepted',
                url=f"/blood-requests/{blood_request.id}/"
            )
            messages.success(request, 'Thank you! You have accepted this blood request. The requester has been notified with your contact details.')
        else:
            messages.info(request, 'You have declined this request.')

    return redirect('blood_requests:request_detail', request_id=request_id)


@login_required
def complete_blood_request_view(request, request_id):
    """
    Mark a blood donation as completed/fulfilled.
    Can be performed by requester, hospital, donor, or admin.
    """
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    user = request.user

    is_owner = (user == blood_request.requester or user.is_staff or user.is_admin)

    # Get donor ID if specified
    donor_id = request.POST.get('donor_id')
    if donor_id:
        target_donor_response = get_object_or_404(RequestResponse, request=blood_request, donor_id=donor_id)
    elif user.is_donor:
        target_donor_response = get_object_or_404(RequestResponse, request=blood_request, donor=user)
    elif is_owner:
        target_donor_response = blood_request.responses.filter(status='accepted').first()
        if not target_donor_response:
            messages.error(request, 'No accepted donor found for this request.')
            return redirect('blood_requests:request_detail', request_id=request_id)
    else:
        messages.error(request, 'Unauthorized action.')
        return redirect('blood_requests:request_detail', request_id=request_id)

    # Complete donation logic
    target_donor_response.status = 'donated'
    target_donor_response.save(update_fields=['status'])

    blood_request.units_fulfilled += 1
    if blood_request.units_fulfilled >= blood_request.units_required:
        blood_request.status = 'fulfilled'
    else:
        blood_request.status = 'in_progress'
    blood_request.save(update_fields=['units_fulfilled', 'status'])

    donor_user = target_donor_response.donor
    donor_profile = getattr(donor_user, 'donor_profile', None)

    if donor_profile:
        donor_profile.last_donation_date = timezone.now().date()
        donor_profile.total_donations += 1
        donor_profile.save(update_fields=['last_donation_date', 'total_donations'])

    # Update recipient/hospital stats
    if blood_request.requester.is_recipient:
        rec_prof = getattr(blood_request.requester, 'recipient_profile', None)
        if rec_prof:
            rec_prof.total_fulfilled += 1
            rec_prof.save(update_fields=['total_fulfilled'])
    elif blood_request.requester.is_hospital:
        hosp_prof = getattr(blood_request.requester, 'hospital_profile', None)
        if hosp_prof:
            hosp_prof.total_donations_facilitated += 1
            hosp_prof.save(update_fields=['total_donations_facilitated'])

    # Create official DonationRecord for certificate generation
    rec_record = DonationRecord.objects.create(
        donor=donor_user,
        recipient=blood_request.requester,
        blood_request=blood_request,
        hospital_name=blood_request.hospital_name,
        blood_group=blood_request.blood_group,
        units_donated=1,
        donation_date=timezone.now().date(),
        is_verified=True,
        verified_by=user if user.is_staff else None
    )

    # Notify donor
    Notification.objects.create(
        user=donor_user,
        title='Donation Completed! Certificate Ready 🏆',
        message=f"Thank you for donating blood for patient {blood_request.patient_name} at {blood_request.hospital_name}! Your certificate (ID: {rec_record.certificate_id}) is ready to download.",
        notification_type='donation_completed',
        url=f"/reports/dashboard/"
    )

    # Notify requester
    Notification.objects.create(
        user=blood_request.requester,
        title='Donation Marked Complete',
        message=f"The blood donation by {donor_user.get_full_name()} for request {blood_request.blood_group} has been marked as complete.",
        notification_type='donation_completed',
        url=f"/blood-requests/{blood_request.id}/"
    )

    messages.success(request, f'Donation completed successfully! Official record and appreciation certificate (ID: {rec_record.certificate_id}) generated.')
    return redirect('blood_requests:request_detail', request_id=request_id)


@login_required
def cancel_blood_request_view(request, request_id):
    """Cancel a pending blood request."""
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    user = request.user

    if user != blood_request.requester and not (user.is_staff or user.is_admin):
        messages.error(request, 'You do not have permission to cancel this request.')
        return redirect('blood_requests:request_detail', request_id=request_id)

    blood_request.status = 'cancelled'
    blood_request.save(update_fields=['status'])

    # Update any accepted responses
    responses = blood_request.responses.filter(status__in=['pending', 'accepted'])
    for resp in responses:
        resp.status = 'cancelled'
        resp.save(update_fields=['status'])
        Notification.objects.create(
            user=resp.donor,
            title='Blood Request Cancelled',
            message=f"The blood request for {blood_request.blood_group} at {blood_request.hospital_name} was cancelled by the requester.",
            notification_type='general',
            url=f"/blood-requests/{blood_request.id}/"
        )

    messages.info(request, 'Blood request has been cancelled.')
    return redirect('blood_requests:request_detail', request_id=request_id)
