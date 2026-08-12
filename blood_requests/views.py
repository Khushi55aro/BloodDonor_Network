"""
Views for blood request creation, listing, details, donor response, and cancellation.
Enforces strict privacy and role-based access control.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import BloodRequest, RequestResponse
from .forms import BloodRequestForm
from .utils import find_and_notify_eligible_donors, haversine_distance, BLOOD_COMPATIBILITY
from donors.models import DonorProfile
from notifications.models import Notification


@login_required
def create_blood_request_view(request):
    """Create a new blood request and trigger Geo-matching."""
    if not (request.user.is_recipient or request.user.is_admin):
        messages.error(request, 'Only recipients can create blood requests.')
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.requester = request.user

            # Fallback to user location if not provided
            if blood_request.latitude is None or blood_request.longitude is None:
                blood_request.latitude = request.user.latitude
                blood_request.longitude = request.user.longitude

            blood_request.save()

            # Execute Geo-matching algorithm & notification broadcast
            notified_count = find_and_notify_eligible_donors(blood_request, radius_km=30)

            if notified_count > 0:
                messages.success(request, f'Blood request created! Geo-matching found and notified {notified_count} nearby eligible donor(s).')
            else:
                messages.warning(request, 'Blood request created! No eligible nearby donors found within 30 km right now.')

            return redirect('blood_requests:request_detail', request_id=blood_request.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BloodRequestForm(initial={
            'latitude': request.user.latitude,
            'longitude': request.user.longitude,
            'address': request.user.address or '',
        })

    return render(request, 'blood_requests/create_request.html', {'form': form})


@login_required
def request_list_view(request):
    """
    List blood requests with strict privacy filtering:
    - Admin: All requests.
    - Recipient: Only requests created by themselves.
    - Donor: Only requests matched to them via RequestResponse.
    """
    user = request.user

    if user.is_admin:
        requests = BloodRequest.objects.all().order_by('-created_at')
    elif user.is_recipient:
        requests = BloodRequest.objects.filter(requester=user).order_by('-created_at')
    elif user.is_donor:
        matched_request_ids = RequestResponse.objects.filter(donor=user).values_list('request_id', flat=True)
        requests = BloodRequest.objects.filter(id__in=matched_request_ids).order_by('-created_at')
    else:
        requests = BloodRequest.objects.none()

    # Calculate distance for donors
    if user.is_donor and user.latitude and user.longitude:
        for req in requests:
            if req.latitude and req.longitude:
                req.distance = round(haversine_distance(user.latitude, user.longitude, req.latitude, req.longitude), 1)
            else:
                req.distance = None

    return render(request, 'blood_requests/list.html', {'requests': requests})


@login_required
def request_detail_view(request, request_id):
    """
    Blood request details page.
    Privacy rules:
    - Recipient sees their request + summary of matched donors (distance & status only).
    - Matched donor sees request details and Accept/Reject buttons.
    - Recipient sees donor phone ONLY if donor has Accepted.
    """
    blood_request = get_object_or_404(BloodRequest, id=request_id)
    user = request.user

    is_owner = (user == blood_request.requester or user.is_admin)
    is_matched_donor = RequestResponse.objects.filter(request=blood_request, donor=user).exists()

    if not (is_owner or is_matched_donor):
        messages.error(request, 'You do not have permission to view this request.')
        return redirect('blood_requests:list')

    responses = blood_request.responses.all().select_related('donor')
    user_response = responses.filter(donor=user).first() if user.is_donor else None

    # Calculate matched donors summary for the recipient
    matched_donors_info = []
    if is_owner and blood_request.latitude and blood_request.longitude:
        for resp in responses:
            donor_user = resp.donor
            dist = haversine_distance(donor_user.latitude, donor_user.longitude, blood_request.latitude, blood_request.longitude)
            matched_donors_info.append({
            'donor_username': donor_user.username if resp.status == 'Accepted' else 'Matched Donor',
            'status': resp.status,
            'distance': round(dist, 1) if dist is not None else 'N/A',
            'phone': donor_user.phone if resp.status == 'Accepted' else None,
})

    context = {
        'blood_request': blood_request,
        'responses': responses,
        'user_response': user_response,
        'is_owner': is_owner,
        'matched_donors_info': matched_donors_info,
        'matched_count': len(matched_donors_info),
    }
    return render(request, 'blood_requests/detail.html', context)


@login_required
def respond_to_request_view(request, request_id):
    """Donor action to Accept or Reject a matched request."""
    if not request.user.is_donor:
        messages.error(request, 'Only donors can respond to blood requests.')
        return redirect('accounts:dashboard')

    blood_request = get_object_or_404(BloodRequest, id=request_id)
    action = request.POST.get('action')

    response = get_object_or_404(RequestResponse, request=blood_request, donor=request.user)

    if action == 'accept':
        response.status = 'Accepted'
        response.save()

        # Notify recipient
        Notification.objects.create(
            user=blood_request.requester,
            title='Donor Accepted Your Blood Request!',
            message=f"Donor {request.user.username} ({request.user.phone or 'No phone listed'}) accepted your request for {blood_request.blood_group}.",
            notification_type='request_accepted',
            url=f"/blood-requests/{blood_request.id}/"
        )
        messages.success(request, 'You have accepted this blood request. The recipient has been notified.')
    elif action == 'reject':
        response.status = 'Rejected'
        response.save()
        messages.info(request, 'You have declined this request.')

    return redirect('blood_requests:request_detail', request_id=request_id)


@login_required
def cancel_blood_request_view(request, request_id):
    """Recipient action to cancel their own blood request."""
    blood_request = get_object_or_404(BloodRequest, id=request_id)

    if request.user != blood_request.requester and not request.user.is_admin:
        messages.error(request, 'You do not have permission to cancel this request.')
        return redirect('blood_requests:request_detail', request_id=request_id)

    blood_request.status = 'Cancelled'
    blood_request.save(update_fields=['status'])
    messages.info(request, 'Blood request has been cancelled.')
    return redirect('blood_requests:request_detail', request_id=request_id)
