import logging

from django.shortcuts import render, get_object_or_404
from django.views import View
from django.http import JsonResponse

from .models import Farmer, Location, Crop
from apps.core.services.africastalking_service import send_sms

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------ #
# Registration                                                         #
# ------------------------------------------------------------------ #

class RegisterFarmerView(View):
    """Register a new farmer and send them a welcome SMS."""

    def get(self, request):
        return render(request, 'farmers/register.html')

    def post(self, request):
        phone_number = request.POST.get('phone_number', '').strip()
        name = request.POST.get('name', '').strip()
        location_name = request.POST.get('location', '').strip()

        if not phone_number:
            return JsonResponse({'error': 'phone_number is required'}, status=400)

        # Get or create the farmer
        farmer, created = Farmer.objects.get_or_create(
            phone_number=phone_number,
            defaults={'name': name},
        )

        if location_name and created:
            location, _ = Location.objects.get_or_create(name=location_name)
            farmer.location = location
            farmer.save()

        # Send welcome SMS only on first registration
        if created:
            greeting_name = name or 'Farmer'
            message = (
                f"Welcome to Farmer's Companion, {greeting_name}! "
                f"You will receive daily weather alerts, market prices, and crop advice. "
                f"Dial *384*# anytime to access our USSD menu."
            )
            send_sms(phone_number, message)
            logger.info("New farmer registered: %s (%s)", name, phone_number)

        return JsonResponse({
            'status': 'created' if created else 'exists',
            'farmer_id': farmer.pk,
            'phone_number': farmer.phone_number,
            'name': farmer.name,
        })


# ------------------------------------------------------------------ #
# Standard page views                                                  #
# ------------------------------------------------------------------ #

def dashboard(request):
    """Farmer dashboard."""
    farmers = Farmer.objects.select_related('location').order_by('-created_at')[:20]
    return render(request, 'farmers/dashboard.html', {'farmers': farmers})


def profile(request, pk):
    """Farmer profile detail."""
    farmer = get_object_or_404(Farmer, pk=pk)
    return render(request, 'farmers/profile.html', {'farmer': farmer})


def login_view(request):
    """Farmer login page."""
    return render(request, 'farmers/login.html')
