"""
Views for generating and viewing reports, certificates, and exports.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import DonationRecord
import csv

# ReportLab imports for PDF generation
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors


@login_required
def reports_dashboard_view(request):
    """Dashboard to view all user reports and certificates."""
    if request.user.is_admin or request.user.is_staff:
        records = DonationRecord.objects.all().order_by('-donation_date')
    elif request.user.is_donor:
        records = request.user.donation_records.all().order_by('-donation_date')
    else:
        records = DonationRecord.objects.filter(recipient=request.user).order_by("-donation_date")
        
    context = {
        'records': records,
    }
    return render(request, 'reports/dashboard.html', context)


@login_required
def export_donations_csv(request):
    """Export the user's donation history to CSV."""
    if not request.user.is_donor:
        return HttpResponse("Unauthorized", status=401)
        
    records = request.user.donation_records.all().order_by('-donation_date')
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="donations_{request.user.username}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Date', 'Blood Group', 'Units', 'Hospital', 'Certificate ID'])
    
    for record in records:
        writer.writerow([
            record.donation_date,
            record.blood_group,
            record.units_donated,
            record.hospital_name,
            record.certificate_id
        ])
        
    return response


@login_required
def download_certificate_pdf(request, record_id):
    """Generate a PDF certificate for a completed donation."""
    record = get_object_or_404(DonationRecord, id=record_id)
    if not record.is_verified:
        return HttpResponse( "Certificate is not verified yet.", status=403)
    
    # Ensure only the donor or an admin can download it
    if request.user != record.donor and not request.user.is_staff:
        return HttpResponse("Unauthorized", status=401)
        
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Certificate_{record.certificate_id}.pdf"'
    
    # Create the PDF object
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # Draw Certificate
    p.setLineWidth(5)
    p.setStrokeColor(colors.maroon)
    p.rect(20, 20, width - 40, height - 40)
    
    p.setFont("Helvetica-Bold", 36)
    p.setFillColor(colors.maroon)
    p.drawCentredString(width / 2.0, height - 100, "Certificate of Appreciation")
    
    p.setFont("Helvetica", 18)
    p.setFillColor(colors.black)
    p.drawCentredString(width / 2.0, height - 180, "This certificate is proudly presented to")
    
    p.setFont("Helvetica-Bold", 28)
    p.drawCentredString(width / 2.0, height - 240, record.donor.get_full_name())
    
    p.setFont("Helvetica", 16)
    text = f"For the noble act of donating {record.units_donated} unit(s) of {record.blood_group} blood"
    p.drawCentredString(width / 2.0, height - 300, text)
    p.drawCentredString(width / 2.0, height - 330, f"at {record.hospital_name}.")
    
    p.setFont("Helvetica", 14)
    p.drawCentredString(width / 2.0, height - 400, f"Date of Donation: {record.donation_date}")
    p.drawCentredString(width / 2.0, height - 430, f"Certificate ID: {record.certificate_id}")
    
    p.setFont("Helvetica-Oblique", 14)
    p.setFillColor(colors.darkgray)
    p.drawCentredString(width / 2.0, height - 550, "Thank you for saving a life!")
    
    p.showPage()
    p.save()
    
    return response
