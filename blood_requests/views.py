"""
Views for handling blood requests, matching, and emergency broadcasts.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BloodRequest, RequestResponse
from .forms import BloodRequestForm, BloodRequestSearchForm
from donors.models import DonorProfile
from notifications.models import Notification


@login_required
def create_blood_request_view(request):
    """View to create a new blood request and trigger matching/notifications."""
    if not (request.user.is_recipient or request.user.is_hospital):
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

            # Geo-matching & Notifications
            if blood_request.latitude and blood_request.longitude:
                # Find eligible donors with same blood group (simplified matching for now)
                # In a real medical app, O- can give to anyone, etc.
                eligible_donors = DonorProfile.objects.filter(
                    blood_group=blood_request.blood_group
                )
                
                notified_count = 0
                for donor in eligible_donors:
                    if donor.is_eligible and donor.user.latitude and donor.user.longitude:
                        distance = donor.distance_to(blood_request.latitude, blood_request.longitude)
                        # Arbitrary radius of 50km for matching
                        if distance is not None and distance <= 50:
                            # Create a RequestResponse linking the donor and the request
                            RequestResponse.objects.create(
                                request=blood_request,
                                donor=donor.user,
                                distance_km=distance
                            )
                            # Create Notification
                            notification_type = 'emergency' if blood_request.is_emergency else 'new_request'
                            title = 'EMERGENCY Blood Request' if blood_request.is_emergency else 'New Blood Request'
                            Notification.objects.create(
                                user=donor.user,
                                title=f"{title}: {blood_request.blood_group} near you!",
                                message=f"A patient needs {blood_request.units_required} unit(s) of {blood_request.blood_group} blood at {blood_request.hospital_name}.",
                                notification_type=notification_type,
                                url=f"/blood-requests/{blood_request.id}/"
                            )
                            notified_count += 1
                
                messages.success(request, f'Blood request created successfully. Notified {notified_count} nearby donors.')
            else:
                messages.success(request, 'Blood request created successfully, but location coordinates were missing for geo-matching.')

            return redirect('blood_requests:request_detail', request_id=blood_request.id)
    else:
        # Pre-fill hospital details if user is hospital
        initial_data = {}
        if request.user.is_hospital:
            hospital_profile = getattr(request.user, 'hospital_profile', None)
            if hospital_profile:
                initial_data = {
                    'hospital_name': hospital_profile.hospital_name,
                    'hospital_address': request.user.address,
                    'latitude': request.user.latitude,
                    'longitude': request.user.longitude,
                }
        form = BloodRequestForm(initial=initial_data)

    return render(request, 'blood_requests/create_request.html', {'form': form})


@login_required
def request_list_view(request):
    """List and search blood requests."""
    form = BloodRequestSearchForm(request.GET)
    requests = BloodRequest.objects.filter(status__in=['open', 'in_progress']).order_by('-is_emergency', 'required_before')

    if form.is_valid():
        blood_group = form.cleaned_data.get('blood_group')
        urgency = form.cleaned_data.get('urgency')
        
        if blood_group:
            requests = requests.filter(blood_group=blood_group)
        if urgency:
            requests = requests.filter(urgency_level=urgency)
            
    # For donors, highlight nearby requests
    nearby_requests = []
    if request.user.is_donor and request.user.latitude and request.user.longitude:
        for req in requests:
            if req.latitude and req.longitude:
                donor_profile = getattr(request.user, 'donor_profile', None)
                if donor_profile:
                    dist = donor_profile.distance_to(req.latitude, req.longitude)
                    if dist is not None and dist <= 50:
                        req.distance = dist
                        nearby_requests.append(req)
        # Sort by distance
        nearby_requests.sort(key=lambda x: x.distance)

    context = {
        'form': form,
        'requests': requests,
        'nearby_requests': nearby_requests,
    }
    return render(request, 'blood_requests/list.html', context)


@login_required
def request_detail_view(request, request_id):
    """Detailed view of a blood request."""
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    responses = blood_request.responses.all().select_related('donor')
    
    # Check if the current donor has responded
    user_response = None
    if request.user.is_donor:
        user_response = responses.filter(donor=request.user).first()
        
    context = {
        'blood_request': blood_request,
        'responses': responses,
        'user_response': user_response,
    }
    return render(request, 'blood_requests/detail.html', context)


@login_required
def respond_to_request_view(request, request_id):
    """Donor action to accept or reject a request."""
    if not request.user.is_donor:
        return redirect('dashboard:index')
        
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    action = request.POST.get('action')
    
    if action in ['accept', 'reject']:
        response, created = RequestResponse.objects.get_or_create(
            request=blood_request,
            donor=request.user
        )
        response.status = 'accepted' if action == 'accept' else 'rejected'
        response.save()
        
        # Notify the requester
        if action == 'accept':
            Notification.objects.create(
                user=blood_request.requester,
                title='Donor Accepted Request',
                message=f"{request.user.get_full_name()} has accepted your blood request for {blood_request.blood_group}.",
                notification_type='request_accepted',
                url=f"/blood-requests/{blood_request.id}/"
            )
            
            messages.success(request, 'You have accepted the blood request. Thank you for your kindness!')
        else:
            messages.info(request, 'You have declined this request.')
            
    return redirect('blood_requests:request_detail', request_id=request_id)
