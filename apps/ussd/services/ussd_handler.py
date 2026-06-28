"""
USSD session handler — language-first flow with AI integration.

Session flow (Africa's Talking accumulates all input as '*'-joined text)
═══════════════════════════════════════════════════════════════════════════
text=''        → language selection (always English; skipped for returning users)
text='1'–'5'   → language chosen → save → main menu in chosen language

From main menu  (steps[0]=lang_digit, steps[1]=action):
  *1   → Weather sub-menu
  *1*1 → Today's weather with AI farming tip (END)
  *1*2 → 7-day forecast intro (END)
  *2   → Market prices sub-menu
  *2*1 → Maize price (END)
  *2*2 → Beans price (END)
  *2*3 → Cassava price (END)
  *2*4 → Coffee price (END)
  *3   → Pest diagnosis sub-menu
  *3*1 → Yellow/wilting leaves → AI diagnosis (END)
  *3*2 → Holes in leaves       → AI diagnosis (END)
  *3*3 → Stunted growth        → AI diagnosis (END)
  *3*4 → Other (generic prompt) (END)
  *4   → Farming tips sub-menu
  *4*1 → Planting tips (END)
  *4*2 → Pest & disease alerts (END)
  *4*3 → Harvest advice (END)
  *5   → Ask AI sub-menu
  *5*1 → Crop advice AI (END)
  *5*2 → Soil tips AI (END)
  *5*3 → Fertilizer guide AI (END)
  *5*4 → Irrigation tips AI (END)
  *6   → My profile (END)
  *7   → Re-show language menu
  *0   → Exit (END)

Back (0) from any sub-menu returns to main menu.
═══════════════════════════════════════════════════════════════════════════
"""
import logging

from apps.ussd.models import UserLanguagePreference
from .menu_structure import (
    LANGUAGE_MAP,
    language_menu,
    main_menu,
    weather_menu,
    market_menu,
    pest_menu,
    farming_tips_menu,
    ai_menu,
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

    steps = text.split('*') if text else []

    # ── Step 0: first dial — no input yet ───────────────────────────
    if not steps:
        saved_lang = UserLanguagePreference.get_language(phone_number)
        # Returning user with a non-English saved preference skips language step
        if saved_lang and saved_lang != 'en':
            return main_menu(saved_lang)
        return language_menu()

    first = steps[0]

    # ── Step 1: language selection ───────────────────────────────────
    if first in LANGUAGE_MAP and len(steps) == 1:
        lang = LANGUAGE_MAP[first]
        UserLanguagePreference.set_language(phone_number, lang)
        logger.info("Language set to %s for %s", lang, phone_number)
        return main_menu(lang)

    # ── Resolve active language ──────────────────────────────────────
    if first in LANGUAGE_MAP:
        lang = LANGUAGE_MAP[first]
        sub = steps[1:]
    else:
        lang = UserLanguagePreference.get_language(phone_number)
        sub = steps

    if not sub:
        return main_menu(lang)

    action = sub[0]

    # ── 0. Exit ──────────────────────────────────────────────────────
    if action == '0':
        return end_msg("Thank you for using Farmer's Companion. Goodbye!", lang)

    # ── 7. Change language ───────────────────────────────────────────
    # When the user picks "Change Language" from the main menu,
    # show the language selection screen.
    # On the NEXT hop, Africa's Talking accumulates the new choice
    # into sub[1].  We must handle that here — otherwise the router
    # loops back to action='7' forever.
    if action == '7':
        if len(sub) >= 2 and sub[1] in LANGUAGE_MAP:
            # User has already picked a new language on this hop
            new_lang = LANGUAGE_MAP[sub[1]]
            UserLanguagePreference.set_language(phone_number, new_lang)
            logger.info(
                "Language changed via option-7 | %s new=%s", phone_number, new_lang
            )
            return main_menu(new_lang)
        # No language chosen yet — show the selection screen
        logger.info("Showing language re-selection for %s", phone_number)
        return language_menu()

    # ── 1. Weather ──────────────────────────────────────────────────
    if action == '1':
        if len(sub) == 1:
            return weather_menu(lang)
        choice = sub[1]
        if choice == '0':
            return main_menu(lang)
        location = _get_farmer_location(phone_number)
        if choice == '1':
            return _today_weather(location, lang)
        if choice == '2':
            return _forecast_response(location, lang)
        return end_msg("Invalid option. Please try again.", lang)

    # ── 2. Market Prices ────────────────────────────────────────────
    if action == '2':
        if len(sub) == 1:
            return market_menu(lang)
        choice = sub[1]
        if choice == '0':
            return main_menu(lang)
        crops = {'1': 'Maize', '2': 'Beans', '3': 'Cassava', '4': 'Coffee'}
        crop = crops.get(choice)
        if crop:
            return _price_response(crop, lang)
        return end_msg("Invalid choice. Please try again.", lang)

    # ── 3. Pest Diagnosis ───────────────────────────────────────────
    if action == '3':
        if len(sub) == 1:
            return pest_menu(lang)
        choice = sub[1]
        if choice == '0':
            return main_menu(lang)
        symptoms = {
            '1': 'yellow or wilting leaves',
            '2': 'holes in leaves',
            '3': 'stunted growth',
            '4': 'general crop problem',
        }
        symptom = symptoms.get(choice)
        if symptom:
            return _pest_diagnosis(symptom, lang)
        return end_msg("Invalid choice. Please try again.", lang)

    # ── 4. Farming Tips ─────────────────────────────────────────────
    if action == '4':
        if len(sub) == 1:
            return farming_tips_menu(lang)
        choice = sub[1]
        if choice == '0':
            return main_menu(lang)
        return _farming_tip(choice, lang)

    # ── 5. Ask AI ───────────────────────────────────────────────────
    if action == '5':
        if len(sub) == 1:
            return ai_menu(lang)
        choice = sub[1]
        if choice == '0':
            return main_menu(lang)
        return _ai_advice(choice, lang)

    # ── 6. My Profile ───────────────────────────────────────────────
    if action == '6':
        return _profile_response(phone_number, lang)

    return end_msg("Invalid option. Please try again.", lang)


# ------------------------------------------------------------------ #
# Private response builders                                            #
# ------------------------------------------------------------------ #

def _get_farmer_location(phone_number: str) -> str:
    try:
        from apps.farmers.models import Farmer
        f = Farmer.objects.select_related('location').get(phone_number=phone_number)
        if f.location:
            return f.location.name
    except Exception:
        pass
    return 'Kampala'


def _today_weather(location: str, lang: str) -> str:
    try:
        from apps.weather.services.weather_api import get_current_weather
        from .ai_assistant import get_weather_farming_tip
        data = get_current_weather(location)
        tip = get_weather_farming_tip(location, data, lang)

        # Translate all label strings and the weather description
        t_hdr  = translate("Weather in", lang)
        t_temp = translate("Temp", lang)
        t_hum  = translate("Humidity", lang)
        # Translate weather description (e.g. "light rain") from the dict
        desc_en = data['description'].lower().strip()
        desc_translated = translate(desc_en, lang)

        logger.info(
            "Weather response | lang=%s location=%s desc='%s' -> '%s'",
            lang, location, desc_en, desc_translated,
        )

        return (
            f"END {t_hdr} {data['location']}:\n"
            f"{t_temp}: {data['temperature']}°C\n"
            f"{t_hum}: {data['humidity']}%\n"
            f"{desc_translated.capitalize()}\n"
            f"{tip}"
        )
    except Exception as exc:
        logger.warning("Weather response failed: %s", exc)
        return end_msg("Could not retrieve weather right now. Try again later.", lang)


def _forecast_response(location: str, lang: str) -> str:
    try:
        from apps.weather.services.weather_api import get_forecast
        forecasts = get_forecast(location, days=3)
        if not forecasts:
            raise ValueError("No forecast data")
        seen_dates, lines = set(), []
        for entry in forecasts:
            date = entry.get('dt_txt', '')[:10]
            if date and date not in seen_dates and '12:00' in entry.get('dt_txt', ''):
                seen_dates.add(date)
                temp = entry['main']['temp']
                desc_en = entry['weather'][0]['description'].lower()
                desc = translate(desc_en, lang)
                lines.append(f"{date}: {temp}°C, {desc}")
            if len(lines) == 3:
                break
        forecast_label = translate("forecast", lang)
        forecast_text = '\n'.join(lines) or 'No data'
        return f"END {location} {forecast_label}:\n{forecast_text}"
    except Exception as exc:
        logger.warning("Forecast response failed: %s", exc)
        return end_msg("Could not retrieve weather right now. Try again later.", lang)


def _price_response(crop: str, lang: str) -> str:
    try:
        from apps.sms.services.market_data import get_market_prices
        data = get_market_prices(crop, region='Uganda')
        price = data.get('price_per_kg', 'N/A')
        market = data.get('market', 'Kampala')
        source = '~' if data.get('source') == 'baseline' else ''
        translated_crop = translate(f"1. {crop}", lang).lstrip('1. ')
        return (
            f"END {translated_crop}\n"
            f"{source}{price} UGX/kg\n"
            f"{market} market"
        )
    except Exception as exc:
        logger.warning("Price response failed for %s: %s", crop, exc)
        return end_msg("Invalid choice. Please try again.", lang)


def _pest_diagnosis(symptom: str, lang: str) -> str:
    try:
        from .ai_assistant import get_pest_diagnosis
        result = get_pest_diagnosis(symptom, lang)
        return f"END {result}"
    except Exception as exc:
        logger.warning("Pest diagnosis failed: %s", exc)
        return end_msg("AI service is unavailable. Try again later.", lang)


def _farming_tip(choice: str, lang: str) -> str:
    tips_en = {
        '1': (
            "Planting tips: Prepare land 2 weeks early. "
            "Use certified seeds. Plant at start of rains. "
            "Space maize 75x25cm."
        ),
        '2': (
            "Pest alerts: Check for Fall Armyworm on maize. "
            "Spray neem early morning. "
            "Report outbreaks to extension officer."
        ),
        '3': (
            "Harvest advice: Harvest maize when husks are dry. "
            "Dry grain below 13% moisture. "
            "Use hermetic bags for storage."
        ),
    }
    text = tips_en.get(choice)
    if not text:
        return end_msg("Invalid choice. Please try again.", lang)
    return 'END ' + translate(text, lang)


def _ai_advice(choice: str, lang: str) -> str:
    try:
        from .ai_assistant import get_ai_response
        topics = {
            '1': ('crop_advice', {'crop': 'maize'}),
            '2': ('soil_tips', {}),
            '3': ('fertilizer', {}),
            '4': ('irrigation', {}),
        }
        if choice not in topics:
            return end_msg("Invalid choice. Please try again.", lang)
        topic, kwargs = topics[choice]
        result = get_ai_response(topic, language=lang, **kwargs)
        return f"END {result}"
    except Exception as exc:
        logger.warning("AI advice failed for choice=%s: %s", choice, exc)
        return end_msg("AI service is unavailable. Try again later.", lang)


def _profile_response(phone_number: str, lang: str) -> str:
    try:
        from apps.farmers.models import Farmer
        farmer = Farmer.objects.select_related('location').get(phone_number=phone_number)
        location = farmer.location.name if farmer.location else translate('Not set', lang)
        crops = ', '.join(c.name for c in farmer.crops.all()) or translate('None', lang)
        lang_display = dict(UserLanguagePreference.LANGUAGE_CHOICES).get(farmer.language, farmer.language)
        t = lambda s: translate(s, lang) if lang != 'en' else s
        return (
            f"END {t('Name')}: {farmer.name or t('Not set')}\n"
            f"{t('Phone')}: {farmer.phone_number}\n"
            f"{t('Location')}: {location}\n"
            f"{t('Crops')}: {crops}\n"
            f"{t('Language')}: {lang_display}"
        )
    except Exception as exc:
        logger.warning("Profile response failed for %s: %s", phone_number, exc)
        return end_msg(
            "You are not registered yet.\nSend REGISTER <name> via SMS\nor visit our website to sign up.",
            lang,
        )
