from django.http import JsonResponse
from .models import UsageEvent


def usage_summary(request):
    """Return a summary of usage events."""
    total = UsageEvent.objects.count()
    by_channel = {
        'voice': UsageEvent.objects.filter(channel='voice').count(),
        'sms': UsageEvent.objects.filter(channel='sms').count(),
        'ussd': UsageEvent.objects.filter(channel='ussd').count(),
    }
    return JsonResponse({'total': total, 'by_channel': by_channel})
