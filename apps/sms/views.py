from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import logging

logger = logging.getLogger('apps.sms')


@csrf_exempt
def sms_callback(request):
    """Handle incoming SMS from Africa's Talking."""
    if request.method == 'POST':
        from_ = request.POST.get('from', '')
        text = request.POST.get('text', '')
        logger.info(f"Incoming SMS from {from_}: {text}")
        # TODO: delegate to sms_handler service
        return JsonResponse({'status': 'received'})
    return JsonResponse({'error': 'Method not allowed'}, status=405)
