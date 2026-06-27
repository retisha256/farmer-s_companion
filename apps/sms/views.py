import logging

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from apps.core.services.africastalking_service import send_sms
from apps.sms.services.sms_handler import process_incoming_sms

logger = logging.getLogger('apps.sms')


@csrf_exempt
def sms_callback(request):
    """
    Handle incoming SMS from Africa's Talking.
    Africa's Talking POSTs these fields:
        from    – sender's phone number
        to      – your shortcode / virtual number
        text    – message body
        date    – timestamp
        id      – unique message id
    """
    if request.method == 'POST':
        sender = request.POST.get('from', '').strip()
        to = request.POST.get('to', '').strip()
        text = request.POST.get('text', '').strip()
        message_id = request.POST.get('id', '')

        logger.info("Incoming SMS | id=%s from=%s to=%s text='%s'", message_id, sender, to, text)

        if sender and text:
            reply = process_incoming_sms(sender, text)
            if reply:
                send_sms(sender, reply)

        # AT expects a 200 OK — content is ignored
        return JsonResponse({'status': 'received'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)
