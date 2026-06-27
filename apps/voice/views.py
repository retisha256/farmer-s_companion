from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import logging

logger = logging.getLogger('apps.voice')


@csrf_exempt
def voice_callback(request):
    """Handle incoming voice calls from Africa's Talking."""
    if request.method == 'POST':
        session_id = request.POST.get('sessionId', '')
        caller_number = request.POST.get('callerNumber', '')
        logger.info(f"Incoming call: session={session_id}, caller={caller_number}")
        # TODO: delegate to voice_handler service
        response = "<Response><Say>Welcome to Farmer's Companion.</Say></Response>"
        return HttpResponse(response, content_type='application/xml')
    return HttpResponse(status=405)
