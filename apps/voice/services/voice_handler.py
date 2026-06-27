"""Africa's Talking Voice logic."""
import africastalking
from django.conf import settings
import logging

logger = logging.getLogger('apps.voice')

africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
voice = africastalking.Voice


def make_call(phone_number: str, callback_url: str) -> dict:
    """Initiate an outbound call."""
    try:
        response = voice.call(callFrom=settings.AT_SHORTCODE, callTo=[phone_number])
        logger.info(f"Call initiated to {phone_number}: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to initiate call to {phone_number}: {e}")
        raise
