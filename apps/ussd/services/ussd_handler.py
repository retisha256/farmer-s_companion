"""
USSD session handler — with language selection as the first step.

New session flow
─────────────────────────────────────────────────────────────────────
text=''        → language selection menu (always in English)
text='1'       → user chose English   → save preference → main menu
text='2'       → user chose Kiswahili → save preference → main menu
text='3'       → user chose Luganda   → save preference → main menu
text='4'       → user chose Runyankole→ save preference → main menu

From the main menu (lang=<code>):
text='<lang>*1'       → weather sub-menu
text='<lang>*1*1'     → current weather (END)
text='<lang>*2'       → market prices sub-menu
text='<lang>*2*1'     → maize price (END)
text='<lang>*2*2'     → wheat price (END)
text='<lang>*2*3'     → tomato price (END)
text='<lang>*3'       → crop advisory sub-menu
text='<lang>*3*1'     → planting tips (END)
text='<lang>*3*2'     → pest & disease (END)
text='<lang>*3*3'     → harvest advice (END)
text='<lang>*4'       → my profile (END)
text='<lang>*5'       → language selection again (re-entry)
text='<lang>*0'       → exit (END)
─────────────────────────────────────────────────────────────────────
Returning user (language already saved):
  Step 0 is skipped; user goes straight to the main menu.
"""
import logging

from apps.ussd.models import UserLanguagePreference
from .menu_structure import (
    LANGUAGE_MAP,
    language_menu,
    main_menu,
    weather_menu,
    market_menu,
    crop_menu,
    end_msg,
)
from .translations import translate

logger = logging.getLogger('apps.ussd')


def handle_ussd_request(session_id: str, phone_number: str, text: str) -> str:
    """
    Entry point called by the USSD view.
    Returns a CON or END string for Africa's Talking.
    """
    logger.info("USSD | session=%s phone=%s text='%s'", session_id, phone_number, text)

    steps = [s for s in text.split('*')] if text else []

    # ── Step 0: no input yet ────────────────────────────────────────
    if not steps:
        saved_lang = UserLanguagePreference.get_language(phone_number)
        if saved_lang and saved_lang != 'en':
            # Returning user with a non-English preference — skip language step
            return main_menu(saved_lang)
        # New user or English default — show language selection
        return language_menu()

    first = steps[0]

    # ── Step 1: user is choosing a language ─────────────────────────
    if first in LANGUAGE_MAP and len(steps) == 1:
        lang = LANGUAGE_MAP[first]
        UserLanguagePreference.set_language(phone_number, lang)
        logger.info("Language set to %s for %s", lang, phone_number)
        return main_menu(lang)

    # ── Determine active language ────────────────────────────────────
    # After language selection, steps[0] is the language choice digit.
    # All subsequent choices are in steps[1], steps[2], etc.
    if first in LANGUAGE_MAP:
        lang = LANGUAGE_MAP[first]
        sub_steps = steps[1:]
    else:
        # Fallback: use stored preference (handles edge cases)
        lang = UserLanguagePreference.get_language(phone_number)
        sub_steps = steps

    depth = len(sub_steps)

    # ── No sub-step yet → show main menu ────────────────────────────
    if depth == 0:
        return main_menu(lang)

    action = sub_steps[0]

    # ── Exit ─────────────────────────────────────────────────────────
    if action == '0':
        return end_msg("Thank you for using Farmer's Companion. Goodbye!", lang)

    # ── Change language (option 5) ───────────────────────────────────
    if action == '5':
        return language_menu()

    # ── 1. Weather ──────────────────────────────────────────────────
    if action == '1':
        if depth == 1:
            return weather_menu(lang)
        choice = sub_steps[1]
        if choice == '0':
            return main_menu(lang)
        location = _get_farmer_location(phone_number)
        return _weather_response(location, lang)

    # ── 2. Market Prices ────────────────────────────────────────────
    if action == '2':
        if depth == 1:
            return market_menu(lang)
        choice = sub_steps[1]
        if choice == '0':
            return main_menu(lang)
        crops = {'1': 'Maize', '2': 'Wheat', '3': 'Tomatoes'}
        crop = crops.get(choice)
        if crop:
            return _price_response(crop, lang)
        return end_msg("Invalid choice. Please try again.", lang)

    # ── 3. Crop Advisory ────────────────────────────────────────────
    if action == '3':
        if depth == 1:
            return crop_menu(lang)
        choice = sub_steps[1]
        if choice == '0':
            return main_menu(lang)
        return _crop_advice_response(choice, lang)

    # ── 4. My Profile ───────────────────────────────────────────────
    if action == '4':
        return _profile_response(phone_number, lang)

    return end_msg("Invalid option. Please try again.", lang)


# ------------------------------------------------------------------ #
# Private helpers                                                      #
# ------------------------------------------------------------------ #

def _get_farmer_location(phone_number: str) -> str:
    """Return farmer's saved location name, or default to Kampala."""
    try:
        from apps.farmers.models import Farmer
        farmer = Farmer.objects.select_related('location').get(phone_number=phone_number)
        if farmer.location:
            return farmer.location.name
    except Exception:
        pass
    return 'Kampala'


def _weather_response(location: str, lang: str) -> str:
    try:
        from apps.weather.services.weather_api import get_current_weather
        data = get_current_weather(location)
        # Build response with translated label words
        label_loc   = translate("Weather in", lang) if lang != 'en' else "Weather in"
        label_temp  = translate("Temp", lang) if lang != 'en' else "Temp"
        label_hum   = translate("Humidity", lang) if lang != 'en' else "Humidity"
        label_cond  = translate("Conditions", lang) if lang != 'en' else "Conditions"
        return (
            f"END {label_loc} {data['location']}:\n"
            f"{label_temp}: {data['temperature']}°C\n"
            f"{label_hum}: {data['humidity']}%\n"
            f"{label_cond}: {data['description'].capitalize()}"
        )
    except Exception as exc:
        logger.warning("USSD weather lookup failed: %s", exc)
        return end_msg("Could not retrieve weather right now. Try again later.", lang)


def _price_response(crop: str, lang: str) -> str:
    try:
        from apps.sms.services.market_data import get_market_prices
        data = get_market_prices(crop, region='Uganda')
        price = data.get('price_per_kg', 'N/A')
        currency = data.get('currency', 'UGX')
        translated_crop = translate(crop, lang)
        return f"END {translated_crop}:\n{price} {currency}/kg"
    except Exception as exc:
        logger.warning("USSD price lookup failed for %s: %s", crop, exc)
        return end_msg("Invalid choice. Please try again.", lang)


def _crop_advice_response(choice: str, lang: str) -> str:
    advice_en = {
        '1': (
            "Planting tips:\n"
            "- Prepare land 2 weeks before planting.\n"
            "- Use certified seeds.\n"
            "- Plant at the start of the rains.\n"
            "- Space maize 75cm x 25cm."
        ),
        '2': (
            "Pest & Disease Alerts:\n"
            "- Check for Fall Armyworm on maize leaves.\n"
            "- Apply neem-based spray early morning.\n"
            "- Report outbreaks to your local extension officer."
        ),
        '3': (
            "Harvest Advice:\n"
            "- Harvest maize when husks are dry and brown.\n"
            "- Dry grain to below 13% moisture before storage.\n"
            "- Use hermetic bags to prevent post-harvest losses."
        ),
    }
    text = advice_en.get(choice)
    if not text:
        return end_msg("Invalid choice. Please try again.", lang)
    return 'END ' + translate(text, lang)


def _profile_response(phone_number: str, lang: str) -> str:
    try:
        from apps.farmers.models import Farmer
        farmer = Farmer.objects.select_related('location').get(phone_number=phone_number)
        location = farmer.location.name if farmer.location else translate('Not set', lang)
        crops = ', '.join(c.name for c in farmer.crops.all()) or translate('None', lang)
        name_label     = translate('Name', lang)     if lang != 'en' else 'Name'
        phone_label    = translate('Phone', lang)    if lang != 'en' else 'Phone'
        location_label = translate('Location', lang) if lang != 'en' else 'Location'
        crops_label    = translate('Crops', lang)    if lang != 'en' else 'Crops'
        lang_label     = translate('Language', lang) if lang != 'en' else 'Language'
        return (
            f"END {name_label}: {farmer.name or translate('Not set', lang)}\n"
            f"{phone_label}: {farmer.phone_number}\n"
            f"{location_label}: {location}\n"
            f"{crops_label}: {crops}\n"
            f"{lang_label}: {farmer.get_language_display() if hasattr(farmer, 'get_language_display') else farmer.language}"
        )
    except Exception:
        return end_msg(
            "You are not registered yet.\nSend REGISTER <name> via SMS\nor visit our website to sign up.",
            lang,
        )
