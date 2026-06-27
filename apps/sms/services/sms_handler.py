"""
Africa's Talking SMS incoming message handler.

Supported keywords (case-insensitive):
  WEATHER <location>  – get current weather
  PRICE <crop>        – get market price for a crop
  HELP                – list available commands
  REGISTER <name>     – quick self-registration
"""
import logging

from apps.sms.services.market_data import get_market_prices

logger = logging.getLogger('apps.sms')


def process_incoming_sms(sender: str, text: str) -> str | None:
    """
    Parse the incoming SMS text and return a reply string,
    or None if no reply should be sent.
    """
    parts = text.strip().split(None, 1)          # split on first whitespace
    keyword = parts[0].upper() if parts else ''
    argument = parts[1].strip() if len(parts) > 1 else ''

    logger.info("Processing SMS from %s | keyword=%s arg='%s'", sender, keyword, argument)

    if keyword == 'WEATHER':
        return _handle_weather(argument or 'your area')

    elif keyword == 'PRICE':
        return _handle_price(argument or 'maize')

    elif keyword == 'REGISTER':
        return _handle_register(sender, argument)

    elif keyword == 'HELP':
        return (
            "Farmer's Companion commands:\n"
            "WEATHER <location> – weather forecast\n"
            "PRICE <crop>       – market price\n"
            "REGISTER <name>    – register your profile\n"
            "Reply HELP anytime."
        )

    else:
        return (
            "Sorry, I didn't understand that. "
            "Reply HELP for a list of commands."
        )


# ------------------------------------------------------------------ #
# Private helpers                                                      #
# ------------------------------------------------------------------ #

def _handle_weather(location: str) -> str:
    """Return a weather summary for the given location."""
    try:
        # Import here to avoid circular imports
        from apps.weather.services.weather_api import get_current_weather
        data = get_current_weather(location)
        return (
            f"Weather in {data['location']}:\n"
            f"Temp: {data['temperature']}°C\n"
            f"Humidity: {data['humidity']}%\n"
            f"Conditions: {data['description'].capitalize()}"
        )
    except Exception as exc:
        logger.warning("Weather lookup failed for '%s': %s", location, exc)
        return f"Could not get weather for '{location}'. Please try again later."


def _handle_price(crop: str) -> str:
    """Return the current market price for a crop."""
    try:
        data = get_market_prices(crop, region='Uganda')
        if data.get('price_per_kg'):
            return (
                f"Market price for {data['crop'].title()}:\n"
                f"{data['price_per_kg']} {data['currency']}/kg\n"
                f"Source: {data['source']}"
            )
        return f"No price data available for '{crop}' right now."
    except Exception as exc:
        logger.warning("Market price lookup failed for '%s': %s", crop, exc)
        return f"Could not retrieve price for '{crop}'. Please try again later."


def _handle_register(phone_number: str, name: str) -> str:
    """Quick SMS registration."""
    if not name:
        return "To register, reply: REGISTER <your name>"
    try:
        from apps.farmers.models import Farmer
        farmer, created = Farmer.objects.get_or_create(
            phone_number=phone_number,
            defaults={'name': name},
        )
        if created:
            return (
                f"Welcome, {name}! You are now registered with Farmer's Companion. "
                f"Dial *384*# for our USSD menu or reply HELP for SMS commands."
            )
        return f"You are already registered as {farmer.name}."
    except Exception as exc:
        logger.error("Registration via SMS failed for %s: %s", phone_number, exc)
        return "Registration failed. Please try again later."
