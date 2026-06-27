"""
USSD session handler.

Africa's Talking sends a single `text` string that accumulates all
choices joined by '*'.  For example, if the user pressed 1 then 2,
text will be '1*2'.

Session flow:
  ''      → main menu
  1       → weather sub-menu
  1*1     → weather for default location (END)
  2       → market prices sub-menu
  2*1     → maize price (END)
  2*2     → wheat price (END)
  2*3     → tomatoes price (END)
  3       → crop advisory sub-menu
  3*1     → planting tips (END)
  3*2     → pest & disease alerts (END)
  3*3     → harvest advice (END)
  4       → my profile (END — shows registration status)
  0       → exit
"""
import logging

from .menu_structure import MAIN_MENU, WEATHER_MENU, MARKET_MENU, CROP_MENU

logger = logging.getLogger('apps.ussd')


def handle_ussd_request(session_id: str, phone_number: str, text: str) -> str:
    """
    Route the USSD request and return a CON (continue) or END response.
    """
    logger.info("USSD | session=%s phone=%s text='%s'", session_id, phone_number, text)

    # Split accumulated input into individual steps
    steps = text.split('*') if text else []
    depth = len(steps)

    # ── Level 0: main menu ──────────────────────────────────────────
    if depth == 0 or text == '':
        return MAIN_MENU

    first = steps[0]

    # ── Exit ────────────────────────────────────────────────────────
    if first == '0':
        return "END Thank you for using Farmer's Companion. Goodbye!"

    # ── 1. Weather ──────────────────────────────────────────────────
    if first == '1':
        if depth == 1:
            return WEATHER_MENU
        second = steps[1]
        if second == '0':
            return MAIN_MENU
        location = 'Kampala'  # default; TODO: use farmer's saved location
        return _weather_response(location)

    # ── 2. Market Prices ────────────────────────────────────────────
    if first == '2':
        if depth == 1:
            return MARKET_MENU
        second = steps[1]
        crops = {'1': 'Maize', '2': 'Wheat', '3': 'Tomatoes'}
        if second == '0':
            return MAIN_MENU
        crop = crops.get(second)
        if crop:
            return _price_response(crop)
        return "END Invalid choice. Please try again."

    # ── 3. Crop Advisory ────────────────────────────────────────────
    if first == '3':
        if depth == 1:
            return CROP_MENU
        second = steps[1]
        if second == '0':
            return MAIN_MENU
        advice = {
            '1': (
                "END Planting tips:\n"
                "- Prepare land 2 weeks before planting.\n"
                "- Use certified seeds.\n"
                "- Plant at the start of the rains.\n"
                "- Space maize 75cm x 25cm."
            ),
            '2': (
                "END Pest & Disease Alerts:\n"
                "- Check for Fall Armyworm on maize leaves.\n"
                "- Apply neem-based spray early morning.\n"
                "- Report outbreaks to your local extension officer."
            ),
            '3': (
                "END Harvest Advice:\n"
                "- Harvest maize when husks are dry and brown.\n"
                "- Dry grain to below 13% moisture before storage.\n"
                "- Use hermetic bags to prevent post-harvest losses."
            ),
        }
        reply = advice.get(second)
        if reply:
            return reply
        return "END Invalid choice. Please try again."

    # ── 4. My Profile ───────────────────────────────────────────────
    if first == '4':
        return _profile_response(phone_number)

    return "END Invalid option. Please try again."


# ------------------------------------------------------------------ #
# Private helpers                                                      #
# ------------------------------------------------------------------ #

def _weather_response(location: str) -> str:
    try:
        from apps.weather.services.weather_api import get_current_weather
        data = get_current_weather(location)
        return (
            f"END Weather in {data['location']}:\n"
            f"Temp: {data['temperature']}°C\n"
            f"Humidity: {data['humidity']}%\n"
            f"Conditions: {data['description'].capitalize()}"
        )
    except Exception as exc:
        logger.warning("USSD weather lookup failed: %s", exc)
        return "END Could not retrieve weather right now. Try again later."


def _price_response(crop: str) -> str:
    try:
        from apps.sms.services.market_data import get_market_prices
        data = get_market_prices(crop, region='Uganda')
        price = data.get('price_per_kg', 'N/A')
        currency = data.get('currency', 'UGX')
        return f"END {crop} market price:\n{price} {currency}/kg\nSource: {data.get('source', 'N/A')}"
    except Exception as exc:
        logger.warning("USSD market price lookup failed for %s: %s", crop, exc)
        return f"END Could not retrieve price for {crop} right now."


def _profile_response(phone_number: str) -> str:
    try:
        from apps.farmers.models import Farmer
        farmer = Farmer.objects.get(phone_number=phone_number)
        location = farmer.location.name if farmer.location else 'Not set'
        crops = ', '.join(c.name for c in farmer.crops.all()) or 'None'
        return (
            f"END Your Profile:\n"
            f"Name: {farmer.name or 'Not set'}\n"
            f"Phone: {farmer.phone_number}\n"
            f"Location: {location}\n"
            f"Crops: {crops}"
        )
    except Exception:
        return (
            "END You are not registered yet.\n"
            "Send REGISTER <name> via SMS\n"
            "or visit our website to sign up."
        )
