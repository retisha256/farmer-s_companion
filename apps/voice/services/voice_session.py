"""
Voice session handler for Farmer's Companion.

How Africa's Talking voice sessions work
─────────────────────────────────────────
Unlike USSD (which accumulates all input as one string), each voice
hop is a SEPARATE POST request.  AT sends:

  isActive       '1' (ongoing) or '0' (ended)
  sessionId      unique session ID
  callerNumber   farmer's phone
  direction      'inbound' or 'outbound'
  dtmfDigits     the digit(s) the farmer pressed (may be absent)
  durationInSeconds  call duration so far

Session state is stored in the database (VoiceSession model) because
each hop is a new HTTP request — there is no Django session cookie.

State machine
─────────────
INIT           → LANGUAGE_SELECT   (first hop, no digit yet)
LANGUAGE_SELECT → MAIN_MENU         (digit 1-5 received)
MAIN_MENU       → WEATHER_MENU      (digit 1)
                → MARKET_MENU       (digit 2)
                → PEST_MENU         (digit 3)
                → FARMING_TIPS      (digit 4)
                → AI_MENU           (digit 5)
                → LANGUAGE_SELECT   (digit 7)
                → HANGUP            (digit 0)
WEATHER_MENU    → weather result    (digit 1 or 2)
                → MAIN_MENU         (digit 0)
MARKET_MENU     → price result      (digit 1-4)
                → MAIN_MENU         (digit 0)
PEST_MENU       → diagnosis result  (digit 1-3)
                → MAIN_MENU         (digit 0)
AI_MENU         → ai result         (digit 1-4)
                → MAIN_MENU         (digit 0)
"""
import logging

from apps.ussd.models import UserLanguagePreference
from apps.voice.models import VoiceSession
from .voice_menu import (
    language_selection_xml,
    main_menu_xml,
    weather_menu_xml,
    market_menu_xml,
    pest_menu_xml,
    ai_menu_xml,
    speak_and_return_xml,
    speak_and_hangup_xml,
    GOODBYE_TEXT,
    LANGUAGE_NAMES,
)

logger = logging.getLogger('apps.voice')

LANGUAGE_MAP = {'1': 'en', '2': 'sw', '3': 'lg', '4': 'rn', '5': 'ac'}

# State constants
INIT            = 'INIT'
LANGUAGE_SELECT = 'LANGUAGE_SELECT'
MAIN_MENU       = 'MAIN_MENU'
WEATHER_MENU    = 'WEATHER_MENU'
MARKET_MENU     = 'MARKET_MENU'
PEST_MENU       = 'PEST_MENU'
FARMING_TIPS    = 'FARMING_TIPS'
AI_MENU         = 'AI_MENU'
HANGUP          = 'HANGUP'


def handle_voice_request(
    session_id: str,
    caller_number: str,
    is_active: str,
    dtmf_digits: str,
    direction: str = 'inbound',
) -> str:
    """
    Main entry point. Returns AT ActionScript XML.
    Called by the voice view on every POST from Africa's Talking.
    """
    logger.info(
        "Voice | session=%s caller=%s active=%s dtmf='%s'",
        session_id, caller_number, is_active, dtmf_digits,
    )

    # Call ended
    if is_active == '0':
        _close_session(session_id)
        logger.info("Voice | call ended session=%s", session_id)
        return speak_and_hangup_xml('')   # AT ignores response when call ends

    # Get or create session
    session = _get_or_create_session(session_id, caller_number, direction)
    state = session.state
    lang = session.language

    logger.info("Voice | state=%s lang=%s", state, lang)

    # ── INIT / LANGUAGE_SELECT ────────────────────────────────────────
    if state in (INIT, LANGUAGE_SELECT):
        if not dtmf_digits:
            # First hop — show language menu
            _update_session(session, state=LANGUAGE_SELECT)
            saved_lang = UserLanguagePreference.get_language(caller_number)
            if saved_lang and saved_lang != 'en':
                # Returning user — skip language selection
                _update_session(session, state=MAIN_MENU, language=saved_lang)
                return main_menu_xml(saved_lang)
            return language_selection_xml()

        if dtmf_digits in LANGUAGE_MAP:
            lang = LANGUAGE_MAP[dtmf_digits]
            UserLanguagePreference.set_language(caller_number, lang)
            _update_session(session, state=MAIN_MENU, language=lang)
            logger.info("Voice | language set to %s for %s", lang, caller_number)
            return main_menu_xml(lang)

        # Invalid digit — replay language menu
        return language_selection_xml()

    # ── MAIN_MENU ────────────────────────────────────────────────────
    if state == MAIN_MENU:
        if dtmf_digits == '0':
            _update_session(session, state=HANGUP)
            return speak_and_hangup_xml(GOODBYE_TEXT.get(lang, GOODBYE_TEXT['en']))
        if dtmf_digits == '1':
            _update_session(session, state=WEATHER_MENU)
            return weather_menu_xml(lang)
        if dtmf_digits == '2':
            _update_session(session, state=MARKET_MENU)
            return market_menu_xml(lang)
        if dtmf_digits == '3':
            _update_session(session, state=PEST_MENU)
            return pest_menu_xml(lang)
        if dtmf_digits == '4':
            _update_session(session, state=FARMING_TIPS)
            return _farming_tips_menu_xml(lang)
        if dtmf_digits == '5':
            _update_session(session, state=AI_MENU)
            return ai_menu_xml(lang)
        if dtmf_digits == '7':
            _update_session(session, state=LANGUAGE_SELECT)
            return language_selection_xml()
        # No digit yet or invalid — replay main menu
        return main_menu_xml(lang)

    # ── WEATHER_MENU ─────────────────────────────────────────────────
    if state == WEATHER_MENU:
        if dtmf_digits == '0':
            _update_session(session, state=MAIN_MENU)
            return main_menu_xml(lang)
        location = _get_farmer_location(caller_number)
        if dtmf_digits == '1':
            msg = _weather_message(location, lang)
            _update_session(session, state=MAIN_MENU)
            return speak_and_return_xml(msg, main_menu_xml(lang))
        if dtmf_digits == '2':
            msg = _forecast_message(location, lang)
            _update_session(session, state=MAIN_MENU)
            return speak_and_return_xml(msg, main_menu_xml(lang))
        return weather_menu_xml(lang)

    # ── MARKET_MENU ──────────────────────────────────────────────────
    if state == MARKET_MENU:
        if dtmf_digits == '0':
            _update_session(session, state=MAIN_MENU)
            return main_menu_xml(lang)
        crops = {'1': 'Maize', '2': 'Beans', '3': 'Cassava', '4': 'Coffee'}
        crop = crops.get(dtmf_digits)
        if crop:
            msg = _price_message(crop, lang)
            _update_session(session, state=MAIN_MENU)
            return speak_and_return_xml(msg, main_menu_xml(lang))
        return market_menu_xml(lang)

    # ── PEST_MENU ────────────────────────────────────────────────────
    if state == PEST_MENU:
        if dtmf_digits == '0':
            _update_session(session, state=MAIN_MENU)
            return main_menu_xml(lang)
        symptoms = {
            '1': 'yellow or wilting leaves',
            '2': 'holes in leaves',
            '3': 'stunted growth',
        }
        symptom = symptoms.get(dtmf_digits)
        if symptom:
            msg = _pest_message(symptom, lang)
            _update_session(session, state=MAIN_MENU)
            return speak_and_return_xml(msg, main_menu_xml(lang))
        return pest_menu_xml(lang)

    # ── FARMING_TIPS ─────────────────────────────────────────────────
    if state == FARMING_TIPS:
        if dtmf_digits == '0':
            _update_session(session, state=MAIN_MENU)
            return main_menu_xml(lang)
        tips = {
            '1': (
                "Planting tips: Prepare your land two weeks before planting. "
                "Use certified seeds and plant at the start of the rains. "
                "Space maize plants 75 by 25 centimeters."
            ),
            '2': (
                "Pest alerts: Check your maize for Fall Armyworm. "
                "Spray neem solution early in the morning. "
                "Report any outbreaks to your local extension officer."
            ),
            '3': (
                "Harvest advice: Harvest maize when the husks are dry and brown. "
                "Dry the grain below 13 percent moisture before storage. "
                "Use hermetic bags to prevent losses."
            ),
        }
        tip = tips.get(dtmf_digits)
        if tip:
            _update_session(session, state=MAIN_MENU)
            return speak_and_return_xml(tip, main_menu_xml(lang))
        return _farming_tips_menu_xml(lang)

    # ── AI_MENU ──────────────────────────────────────────────────────
    if state == AI_MENU:
        if dtmf_digits == '0':
            _update_session(session, state=MAIN_MENU)
            return main_menu_xml(lang)
        topics = {
            '1': ('crop_advice', {'crop': 'maize'}),
            '2': ('soil_tips', {}),
            '3': ('fertilizer', {}),
            '4': ('irrigation', {}),
        }
        entry = topics.get(dtmf_digits)
        if entry:
            topic, kwargs = entry
            msg = _ai_message(topic, lang, **kwargs)
            _update_session(session, state=MAIN_MENU)
            return speak_and_return_xml(msg, main_menu_xml(lang))
        return ai_menu_xml(lang)

    # Fallback
    _update_session(session, state=MAIN_MENU)
    return main_menu_xml(lang)


# ------------------------------------------------------------------ #
# Session management                                                   #
# ------------------------------------------------------------------ #

def _get_or_create_session(
    session_id: str, caller_number: str, direction: str
) -> 'VoiceSession':
    session, created = VoiceSession.objects.get_or_create(
        session_id=session_id,
        defaults={
            'caller_number': caller_number,
            'direction': direction,
            'state': INIT,
            'language': UserLanguagePreference.get_language(caller_number),
        },
    )
    if created:
        logger.info("Voice | new session created: %s", session_id)
    return session


def _update_session(session: 'VoiceSession', **kwargs) -> None:
    for key, value in kwargs.items():
        setattr(session, key, value)
    session.save(update_fields=list(kwargs.keys()) + ['updated_at'])


def _close_session(session_id: str) -> None:
    VoiceSession.objects.filter(session_id=session_id).update(is_active=False)


# ------------------------------------------------------------------ #
# Farming tips menu XML (not in voice_menu to keep it thin)           #
# ------------------------------------------------------------------ #

def _farming_tips_menu_xml(lang: str) -> str:
    from .voice_menu import _xml, _get_digits, _callback_url
    texts = {
        'en': "Press 1 for planting tips. Press 2 for pest alerts. Press 3 for harvest advice. Press 0 to go back.",
        'sw': "Bonyeza 1 kwa kupanda. Bonyeza 2 kwa wadudu. Bonyeza 3 kwa mavuno. Bonyeza 0 kurudi.",
        'lg': "Nyiga 1 ku okusiga. Nyiga 2 ku ensowera. Nyiga 3 ku okuŋŋaba. Nyiga 0 okuddayo.",
        'rn': "Kanda 1 gutera. Kanda 2 indwara. Kanda 3 gusarura. Kanda 0 gusubira.",
        'ac': "Ket 1 cibo cek. Ket 2 kite. Ket 3 kayo. Ket 0 dok.",
    }
    text = texts.get(lang, texts['en'])
    return _xml(_get_digits(text, _callback_url('/voice/callback/')))


# ------------------------------------------------------------------ #
# Response message builders                                            #
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


def _weather_message(location: str, lang: str) -> str:
    try:
        from apps.weather.services.weather_api import get_current_weather
        from apps.ussd.services.ai_assistant import get_weather_farming_tip
        data = get_current_weather(location)
        tip = get_weather_farming_tip(location, data, 'en')  # tip always English for TTS
        return (
            f"Weather in {data['location']}. "
            f"Temperature {data['temperature']} degrees Celsius. "
            f"Humidity {data['humidity']} percent. "
            f"{data['description'].capitalize()}. "
            f"Farming tip: {tip}"
        )
    except Exception as exc:
        logger.warning("Voice weather failed: %s", exc)
        return "Sorry, weather information is not available right now. Please try again later."


def _forecast_message(location: str, lang: str) -> str:
    try:
        from apps.weather.services.weather_api import get_forecast
        forecasts = get_forecast(location, days=3)
        lines = []
        seen = set()
        for entry in forecasts:
            date = entry.get('dt_txt', '')[:10]
            if date and date not in seen and '12:00' in entry.get('dt_txt', ''):
                seen.add(date)
                temp = entry['main']['temp']
                desc = entry['weather'][0]['description']
                lines.append(f"On {date}: {temp} degrees, {desc}.")
            if len(lines) == 3:
                break
        return f"3-day forecast for {location}. " + ' '.join(lines)
    except Exception as exc:
        logger.warning("Voice forecast failed: %s", exc)
        return "Sorry, forecast information is not available right now."


def _price_message(crop: str, lang: str) -> str:
    try:
        from apps.sms.services.market_data import get_market_prices
        data = get_market_prices(crop, region='Uganda')
        price = data.get('price_per_kg', 'unknown')
        market = data.get('market', 'Kampala')
        source = 'estimated' if data.get('source') == 'baseline' else 'current'
        return (
            f"{crop} {source} price in {market}: "
            f"{price} Uganda shillings per kilogram."
        )
    except Exception as exc:
        logger.warning("Voice price failed for %s: %s", crop, exc)
        return f"Sorry, price information for {crop} is not available right now."


def _pest_message(symptom: str, lang: str) -> str:
    try:
        from apps.ussd.services.ai_assistant import get_pest_diagnosis
        return get_pest_diagnosis(symptom, 'en')   # always English for TTS clarity
    except Exception as exc:
        logger.warning("Voice pest diagnosis failed: %s", exc)
        return "Sorry, the pest diagnosis service is not available right now."


def _ai_message(topic: str, lang: str, **kwargs) -> str:
    try:
        from apps.ussd.services.ai_assistant import get_ai_response
        return get_ai_response(topic, language='en', **kwargs)  # English for TTS
    except Exception as exc:
        logger.warning("Voice AI advice failed topic=%s: %s", topic, exc)
        return "Sorry, AI advice is not available right now."
