"""USSD menu logic."""
from .menu_structure import MAIN_MENU, WEATHER_MENU, MARKET_MENU, CROP_MENU
import logging

logger = logging.getLogger('apps.ussd')


def handle_ussd_request(session_id: str, phone_number: str, text: str) -> str:
    """
    Route a USSD request to the correct menu based on the text input.
    Returns a USSD response string starting with CON (continue) or END.
    """
    logger.info(f"USSD request: session={session_id}, phone={phone_number}, text='{text}'")

    if text == '':
        return MAIN_MENU
    elif text == '1':
        return WEATHER_MENU
    elif text == '2':
        return MARKET_MENU
    elif text == '3':
        return CROP_MENU
    elif text == '0':
        return "END Thank you for using Farmer's Companion."
    else:
        return "END Invalid option. Please try again."
