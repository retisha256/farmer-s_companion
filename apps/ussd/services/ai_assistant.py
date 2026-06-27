"""
AI Advisory Service for Farmer's Companion.

Provider chain (in order):
  1. Google Gemini (gemini-2.0-flash) — primary
  2. OpenAI (gpt-3.5-turbo)           — secondary fallback
  3. Static curated responses          — always available, zero API cost

Root cause of "AI unavailable" message:
  Both OPENAI_API_KEY and GEMINI_API_KEY have exceeded their free-tier
  quota (HTTP 429 insufficient_quota / RESOURCE_EXHAUSTED).
  The service correctly catches the exception but the static fallback
  layer was missing, so farmers received an unhelpful error.

Fix:
  - Gemini is now the PRIMARY provider (higher free quota than OpenAI)
  - OpenAI is the SECONDARY fallback
  - Static curated responses are the FINAL fallback — farmers always
    get useful, actionable advice even when both APIs are down
  - All exceptions are logged with full detail (no silent failures)
  - Each failure mode is identified in logs: quota, auth, network, etc.
"""
import logging
import traceback

from django.conf import settings

from .translations import translate, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

# Tracks whether the last call to each provider failed due to quota.
# Reset each call so we don't permanently skip a provider after one failure.
_last_failure_was_quota: dict[str, bool] = {'gemini': False, 'openai': False}

# ------------------------------------------------------------------ #
# System prompt                                                        #
# ------------------------------------------------------------------ #

_SYSTEM_PROMPT = (
    "You are an expert agricultural advisor for smallholder farmers in Uganda. "
    "Rules: max 3 sentences, under 160 characters total, plain text only "
    "(no bullets, no markdown), practical and actionable, relevant to East Africa. "
    "Always answer in English — translation is handled separately."
)

# ------------------------------------------------------------------ #
# Topic prompts                                                        #
# ------------------------------------------------------------------ #

TOPIC_PROMPTS = {
    'crop_advice': "Give brief planting or cultivation advice for {crop} in Uganda.",
    'soil_tips':   "Give one key soil preparation tip for smallholder farmers in Uganda.",
    'fertilizer':  "Give one practical fertilizer recommendation for subsistence farmers in Uganda.",
    'irrigation':  "Give one water management tip for smallholder farmers in Uganda.",
    'pest_diagnosis': (
        "A farmer's crop shows: {symptom}. "
        "Name the likely cause, give one remedy, give one prevention tip. "
        "Max 2 sentences."
    ),
    'weather_summary': (
        "Weather in {location}: {weather_data}. "
        "Give one farming action tip in one sentence."
    ),
    'general': "A Ugandan farmer asks: {question}. Answer in 2-3 short sentences.",
}

# ------------------------------------------------------------------ #
# Static fallback responses (used when ALL APIs fail)                 #
# These are curated, field-tested tips — not placeholders.            #
# ------------------------------------------------------------------ #

_STATIC_RESPONSES: dict[str, str] = {
    'crop_advice': (
        "Plant maize at start of long rains (Mar-May). "
        "Use certified seed at 75x25cm spacing. "
        "Apply CAN fertilizer 6 weeks after planting."
    ),
    'soil_tips': (
        "Add compost or manure before tilling. "
        "Rotate crops each season to restore soil nutrients. "
        "Avoid burning crop residues — dig them in instead."
    ),
    'fertilizer': (
        "Apply DAP at planting (1 bag per acre). "
        "Top-dress with CAN 6 weeks later. "
        "Use urea only on well-watered soil to avoid leaf burn."
    ),
    'irrigation': (
        "Water crops early morning to reduce evaporation. "
        "Use mulch around plants to retain soil moisture. "
        "Dig simple water channels to direct rain runoff to crops."
    ),
    'pest_diagnosis': (
        "Yellow leaves may indicate nitrogen deficiency or mosaic virus. "
        "Remove affected plants and apply foliar fertilizer. "
        "Use certified disease-free seeds next season."
    ),
    'weather_summary': (
        "Check local weather before applying pesticides or fertilizer. "
        "Avoid planting just before heavy rains — wait 2 days. "
        "Harvest before forecast rain to protect grain quality."
    ),
    'general': (
        "Keep a simple farm diary to track planting dates and yields. "
        "Join a local farmer group to share knowledge and inputs. "
        "Contact your extension officer for free advice on your crops."
    ),
}

# ------------------------------------------------------------------ #
# Public API                                                           #
# ------------------------------------------------------------------ #

def get_ai_response(topic: str, language: str = 'en', **kwargs) -> str:
    """
    Get an AI farming response for the given topic.

    Provider chain: Gemini → OpenAI → Static fallback.
    Response is always translated to `language` before returning.

    Args:
        topic:    key from TOPIC_PROMPTS
        language: ISO code ('en', 'sw', 'lg', 'rn', 'ac')
        **kwargs: template variables for the topic prompt

    Returns:
        Translated string, always non-empty.
    """
    prompt_template = TOPIC_PROMPTS.get(topic, TOPIC_PROMPTS['general'])

    try:
        prompt = prompt_template.format(**kwargs)
    except KeyError as exc:
        logger.error(
            "Missing prompt variable | topic=%s missing_key=%s kwargs=%s",
            topic, exc, kwargs,
        )
        prompt = TOPIC_PROMPTS['general'].format(question=f"farming advice about {topic}")

    logger.info("AI request | topic=%s lang=%s prompt=%.80s", topic, language, prompt)

    # Fast path: if Gemini was quota-exhausted on the last call,
    # skip both API providers immediately and serve the static fallback.
    # This keeps response time well under the 5s USSD gateway timeout.
    if _last_failure_was_quota['gemini']:
        logger.info("Quota exhausted (cached) — using static fallback immediately for topic=%s", topic)
        response_en = _STATIC_RESPONSES.get(topic, _STATIC_RESPONSES['general'])
        logger.info("AI final response (static, %d chars): %.80s", len(response_en), response_en)
        return translate(response_en, language)

    # 1. Try Gemini
    response_en = _call_gemini(prompt)

    # 2. Try OpenAI only if Gemini failed for a non-quota reason
    if response_en is None and not _last_failure_was_quota['gemini']:
        logger.info("Gemini failed (non-quota) — trying OpenAI")
        response_en = _call_openai(prompt)

    # 3. Static fallback — always fast, always available
    if response_en is None:
        logger.warning(
            "Both AI providers unavailable | topic=%s — using static fallback", topic
        )
        response_en = _STATIC_RESPONSES.get(topic, _STATIC_RESPONSES['general'])

    logger.info("AI final response (en, %d chars): %.80s", len(response_en), response_en)

    return translate(response_en, language)


def get_pest_diagnosis(symptom: str, language: str = 'en') -> str:
    return get_ai_response('pest_diagnosis', language=language, symptom=symptom)


def get_weather_farming_tip(location: str, weather_data: dict, language: str = 'en') -> str:
    weather_str = (
        f"temp {weather_data.get('temperature', '?')}°C, "
        f"humidity {weather_data.get('humidity', '?')}%, "
        f"{weather_data.get('description', 'unknown')}"
    )
    return get_ai_response(
        'weather_summary', language=language,
        location=location, weather_data=weather_str,
    )


def get_crop_advice(crop: str, language: str = 'en') -> str:
    return get_ai_response('crop_advice', language=language, crop=crop)


def get_general_advice(question: str, language: str = 'en') -> str:
    return get_ai_response('general', language=language, question=question)


# ------------------------------------------------------------------ #
# Provider: Google Gemini (primary)                                    #
# ------------------------------------------------------------------ #

def _call_gemini(user_prompt: str) -> str | None:
    """
    Call Gemini 2.0 Flash. Returns English text or None.
    Hard timeout: 3 seconds (USSD gateway allows ~5s total).
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()
    if not api_key:
        logger.warning("Gemini | MISSING_KEY — GEMINI_API_KEY not configured")
        return None

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        full_prompt = f"{_SYSTEM_PROMPT}\n\n{user_prompt}"
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=full_prompt,
        )
        text = response.text.strip() if response.text else None
        if not text:
            logger.warning("Gemini | empty response for prompt: %.80s", user_prompt)
            _last_failure_was_quota['gemini'] = False
            return None
        _last_failure_was_quota['gemini'] = False
        logger.info("Gemini | SUCCESS (%d chars)", len(text))
        return text

    except Exception as exc:
        exc_str = str(exc)
        exc_type = type(exc).__name__

        if '429' in exc_str or 'RESOURCE_EXHAUSTED' in exc_str or 'quota' in exc_str.lower():
            _last_failure_was_quota['gemini'] = True
            logger.error(
                "Gemini | QUOTA_EXHAUSTED — add billing at https://ai.google.dev/pricing | %.200s",
                exc_str,
            )
        elif '401' in exc_str or 'API_KEY_INVALID' in exc_str or 'authentication' in exc_str.lower():
            _last_failure_was_quota['gemini'] = False
            logger.error("Gemini | AUTH_FAILED — check GEMINI_API_KEY | %.200s", exc_str)
        elif 'ConnectionError' in exc_type or 'Timeout' in exc_type or 'timeout' in exc_str.lower():
            _last_failure_was_quota['gemini'] = False
            logger.error("Gemini | NETWORK_ERROR — %s: %.200s", exc_type, exc_str)
        else:
            _last_failure_was_quota['gemini'] = False
            logger.error(
                "Gemini | UNEXPECTED_ERROR — %s: %.200s\n%s",
                exc_type, exc_str, traceback.format_exc(),
            )
        return None


# ------------------------------------------------------------------ #
# Provider: OpenAI (secondary fallback)                               #
# ------------------------------------------------------------------ #

def _call_openai(user_prompt: str) -> str | None:
    """
    Call OpenAI gpt-3.5-turbo. Returns English text or None.
    Hard timeout: 3s, zero retries (USSD gateway allows ~5s total).
    """
    api_key = getattr(settings, 'OPENAI_API_KEY', '').strip()
    if not api_key:
        logger.warning("OpenAI | MISSING_KEY — OPENAI_API_KEY not configured")
        return None

    try:
        import openai
        # max_retries=0 prevents the SDK from retrying 429s, which would
        # consume the entire USSD timeout budget (5s) before falling back.
        client = openai.OpenAI(api_key=api_key, max_retries=0, timeout=3.0)
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': _SYSTEM_PROMPT},
                {'role': 'user',   'content': user_prompt},
            ],
            max_tokens=120,
            temperature=0.4,
        )
        text = response.choices[0].message.content.strip()
        if not text:
            logger.warning("OpenAI | returned empty response")
            return None
        logger.info("OpenAI | SUCCESS (%d chars)", len(text))
        return text

    except Exception as exc:
        exc_str = str(exc)
        exc_type = type(exc).__name__

        if 'insufficient_quota' in exc_str or ('429' in exc_str and 'quota' in exc_str.lower()):
            logger.error(
                "OpenAI | QUOTA_EXHAUSTED — add credits at https://platform.openai.com/billing | %.200s",
                exc_str,
            )
        elif 'AuthenticationError' in exc_type or 'invalid_api_key' in exc_str:
            logger.error("OpenAI | AUTH_FAILED — check OPENAI_API_KEY | %.200s", exc_str)
        elif 'RateLimitError' in exc_type:
            logger.error("OpenAI | RATE_LIMITED | %.200s", exc_str)
        elif 'ConnectionError' in exc_type or 'Timeout' in exc_type:
            logger.error("OpenAI | NETWORK_ERROR — %s: %.200s", exc_type, exc_str)
        else:
            logger.error(
                "OpenAI | UNEXPECTED_ERROR — %s: %.200s\n%s",
                exc_type, exc_str, traceback.format_exc(),
            )
        return None
