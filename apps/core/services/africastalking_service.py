"""
Central Africa's Talking service utility.
All AT SDK calls go through here so the rest of the app
never imports africastalking directly.
"""
import logging

import africastalking
from django.conf import settings

logger = logging.getLogger(__name__)


class AfricaTalkingService:
    """
    Wraps the Africa's Talking SDK.
    Initialises once per instance; re-use a single instance
    (or use the module-level helpers below) to avoid repeated init calls.
    """

    def __init__(self):
        africastalking.initialize(
            username=settings.AT_USERNAME,
            api_key=settings.AT_API_KEY,
        )
        self.sms = africastalking.SMS
        self.voice = africastalking.Voice
        # africastalking.USSD is used server-side only for sending USSD push;
        # incoming USSD is handled via webhooks, not this object.

    # ------------------------------------------------------------------ #
    # SMS                                                                  #
    # ------------------------------------------------------------------ #

    def send_sms(self, phone_number: str, message: str, sender_id: str = None) -> dict | None:
        """
        Send an SMS to a single number.
        phone_number should be in international format, e.g. +256700000001
        sender_id defaults to settings.AT_SENDER_ID when not specified.
        """
        sid = sender_id or settings.AT_SENDER_ID or None
        try:
            response = self.sms.send(message, [phone_number], sender_id=sid)
            logger.info("SMS sent to %s | response: %s", phone_number, response)
            return response
        except Exception as exc:
            logger.error("Failed to send SMS to %s: %s", phone_number, exc)
            return None

    def send_bulk_sms(self, recipients: list[str], message: str, sender_id: str = None) -> dict | None:
        """Send the same SMS to multiple numbers."""
        sid = sender_id or settings.AT_SENDER_ID or None
        try:
            response = self.sms.send(message, recipients, sender_id=sid)
            logger.info("Bulk SMS sent to %d recipients | response: %s", len(recipients), response)
            return response
        except Exception as exc:
            logger.error("Failed to send bulk SMS: %s", exc)
            return None

    # ------------------------------------------------------------------ #
    # Voice                                                                #
    # ------------------------------------------------------------------ #

    def make_call(self, phone_number: str) -> dict | None:
        """Initiate an outbound call to phone_number."""
        try:
            response = self.voice.call(
                callFrom=settings.AT_SHORTCODE,
                callTo=[phone_number],
            )
            logger.info("Call initiated to %s | response: %s", phone_number, response)
            return response
        except Exception as exc:
            logger.error("Failed to call %s: %s", phone_number, exc)
            return None


# ------------------------------------------------------------------ #
# Convenience module-level helpers                                     #
# ------------------------------------------------------------------ #

def send_sms(phone_number: str, message: str, sender_id: str = None) -> dict | None:
    """Module-level shortcut — no need to instantiate AfricaTalkingService."""
    return AfricaTalkingService().send_sms(phone_number, message, sender_id)


def send_bulk_sms(recipients: list[str], message: str, sender_id: str = None) -> dict | None:
    """Module-level shortcut for bulk SMS."""
    return AfricaTalkingService().send_bulk_sms(recipients, message, sender_id)
