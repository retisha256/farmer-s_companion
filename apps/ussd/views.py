import logging

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

from .services.ussd_handler import handle_ussd_request

logger = logging.getLogger('apps.ussd')


@csrf_exempt
def ussd_callback(request):
    """
    Handle USSD requests from Africa's Talking.
    Africa's Talking POSTs:
        sessionId   – unique session identifier
        serviceCode – the USSD code dialled, e.g. *384#
        phoneNumber – caller's number in international format
        text        – accumulated input, e.g. '' / '1' / '1*2'
    Response must be plain text starting with CON or END.
    """
    if request.method == 'POST':
        session_id = request.POST.get('sessionId', '')
        service_code = request.POST.get('serviceCode', '')
        phone_number = request.POST.get('phoneNumber', '')
        text = request.POST.get('text', '')

        logger.info(
            "USSD callback | session=%s code=%s phone=%s text='%s'",
            session_id, service_code, phone_number, text,
        )

        response_text = handle_ussd_request(session_id, phone_number, text)
        return HttpResponse(response_text, content_type='text/plain')

    return HttpResponse('Method not allowed', status=405)
