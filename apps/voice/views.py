"""
Voice callback view for Africa's Talking.

AT sends a POST on every call event (answer, DTMF digit, hangup).
We return AT ActionScript XML that tells AT what to speak and collect.
"""
import logging

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from .services.voice_session import handle_voice_request
from .models import VoiceCall

logger = logging.getLogger('apps.voice')


@csrf_exempt
def voice_callback(request):
    """
    Handle all voice events from Africa's Talking.

    AT POSTs these fields:
      isActive          '1' = call live, '0' = call ended
      sessionId         unique session ID
      callerNumber      farmer's number in international format
      destinationNumber your virtual number
      direction         'inbound' or 'outbound'
      dtmfDigits        key(s) pressed (absent if none yet)
      durationInSeconds call duration so far
      callSessionState  e.g. 'Active', 'Completed'
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    session_id    = request.POST.get('sessionId', '')
    caller_number = request.POST.get('callerNumber', '')
    is_active     = request.POST.get('isActive', '1')
    dtmf_digits   = request.POST.get('dtmfDigits', '')
    direction     = request.POST.get('direction', 'inbound')
    duration      = request.POST.get('durationInSeconds', '0')

    logger.info(
        "Voice callback | session=%s caller=%s active=%s dtmf='%s' dur=%ss",
        session_id, caller_number, is_active, dtmf_digits, duration,
    )

    # Log the raw call event for audit purposes
    _log_call_event(session_id, caller_number, direction, duration)

    xml = handle_voice_request(
        session_id=session_id,
        caller_number=caller_number,
        is_active=is_active,
        dtmf_digits=dtmf_digits,
        direction=direction,
    )

    logger.debug("Voice response XML: %s", xml[:200])
    return HttpResponse(xml, content_type='application/xml')


def _log_call_event(session_id, caller_number, direction, duration):
    """Update or create the VoiceCall audit record."""
    try:
        VoiceCall.objects.update_or_create(
            session_id=session_id,
            defaults={
                'caller_number': caller_number,
                'direction': direction,
                'duration': int(duration) if str(duration).isdigit() else 0,
            },
        )
    except Exception as exc:
        logger.warning("Could not log call event: %s", exc)
