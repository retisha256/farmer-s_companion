from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .services.ussd_handler import handle_ussd_request
import logging

logger = logging.getLogger('apps.ussd')


@csrf_exempt
def ussd_callback(request):
    """Handle USSD requests from Africa's Talking."""
    if request.method == 'POST':
        session_id = request.POST.get('sessionId', '')
        phone_number = request.POST.get('phoneNumber', '')
        text = request.POST.get('text', '')
        response_text = handle_ussd_request(session_id, phone_number, text)
        return HttpResponse(response_text, content_type='text/plain')
    return HttpResponse('Method not allowed', status=405)
