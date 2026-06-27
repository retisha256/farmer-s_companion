"""Africa's Talking Voice logic — uses the central AT service."""
import logging

from apps.core.services.africastalking_service import AfricaTalkingService

logger = logging.getLogger('apps.voice')


def make_call(phone_number: str) -> dict | None:
    """Initiate an outbound call to phone_number."""
    return AfricaTalkingService().make_call(phone_number)
