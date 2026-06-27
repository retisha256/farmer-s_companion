"""Africa's Talking SMS logic."""
import africastalking
from django.conf import settings
import logging

logger = logging.getLogger('apps.sms')

africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
sms = africastalking.SMS


def send_sms(recipients: list, message: str) -> dict:
    """Send an SMS to a list of recipients."""
    try:
        response = sms.send(message, recipients, sender_id=settings.AT_SENDER_ID)
        logger.info(f"SMS sent to {recipients}: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        raise
