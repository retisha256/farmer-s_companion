from django.http import JsonResponse


def payment_status(request, transaction_id):
    """Return the status of a payment."""
    # TODO: implement payment lookup
    return JsonResponse({'transaction_id': transaction_id, 'status': 'pending'})
