"""
AI Advisory Service for Farmer's Companion.

Provides farming advice, pest diagnosis, weather summaries,
and general agricultural guidance using OpenAI.

All responses are:
  - Short (≤ 160 chars) to fit on a feature phone screen
  - In plain text (no markdown)
  - Translated to the farmer's language before returning
"""
import logging

from django.conf import settings

from .translations import translate, SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

# System prompt used for all agricultural queries
_SYSTEM_PROMPT = """You are an expert agricultural advisor helping smallholder farmers in Uganda.
Your responses must be:
- Very short (maximum 3 sentences, under 160 characters total)
- In plain text, no bullet points, no markdown
- Practical and actionable
- Relevant to East African farming conditions
Always answer in English — the calling code handles translation."""

# Topic-specific prompts
TOPIC_PROMPTS = {
    'crop_advice': "Give brief planting or cultivation advice for {crop} in Uganda.",
    'soil_tips': "Give one key soil preparation tip for smallholder farmers in Uganda.",
    'fertilizer': "Give one practical fertilizer recommendation for subsistence farmers in Uganda.",
    'irrigation': "Give one water management tip for smallholder farmers in Uganda.",
    'pest_diagnosis': (
        "A farmer's crop shows: {symptom}. "
        "In 2-3 short sentences: name the likely cause, give one remedy, give one prevention tip."
    ),
    'weather_summary': (
        "Given this weather data for {location}: {weather_data}. "
        "Give one farming action tip in one sentence (e.g. delay planting, apply fertilizer)."
    ),
    'general': "A Ugandan farmer asks: {question}. Answer in 2-3 short sentences.",
}


def get_ai_response(topic: str, language: str = 'en', **kwargs) -> str:
    """
    Get an AI-generated farming response.

    Args:
        topic: one of TOPIC_PROMPTS keys
        language: language code for the response
        **kwargs: variables to inject into the topic prompt

    Returns:
        A short translated string, or a fallback message on error.
    """
    prompt_template = TOPIC_PROMPTS.get(topic, TOPIC_PROMPTS['general'])
    try:
        prompt = prompt_template.format(**kwargs)
    except KeyError as exc:
        logger.error("Missing prompt variable for topic=%s: %s", topic, exc)
        return translate("AI service is unavailable. Try again later.", language)

    response_en = _call_openai(prompt)
    if not response_en:
        return translate("AI service is unavailable. Try again later.", language)

    # Translate the English response to the farmer's language
    return translate(response_en, language)


def get_pest_diagnosis(symptom: str, language: str = 'en') -> str:
    """Diagnose a crop problem from a symptom description."""
    return get_ai_response('pest_diagnosis', language=language, symptom=symptom)


def get_weather_farming_tip(location: str, weather_data: dict, language: str = 'en') -> str:
    """Generate a farming action based on current weather."""
    weather_str = (
        f"temp {weather_data.get('temperature', '?')}°C, "
        f"humidity {weather_data.get('humidity', '?')}%, "
        f"{weather_data.get('description', 'unknown conditions')}"
    )
    return get_ai_response(
        'weather_summary', language=language,
        location=location, weather_data=weather_str,
    )


def get_crop_advice(crop: str, language: str = 'en') -> str:
    """Get general crop-specific advice."""
    return get_ai_response('crop_advice', language=language, crop=crop)


def get_general_advice(question: str, language: str = 'en') -> str:
    """Answer a free-form farmer question."""
    return get_ai_response('general', language=language, question=question)


# ------------------------------------------------------------------ #
# Internal                                                             #
# ------------------------------------------------------------------ #

def _call_openai(user_prompt: str) -> str | None:
    """Call OpenAI and return a plain English response, or None on failure."""
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        logger.warning("OPENAI_API_KEY not configured — AI features unavailable")
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role': 'system', 'content': _SYSTEM_PROMPT},
                {'role': 'user', 'content': user_prompt},
            ],
            max_tokens=120,
            temperature=0.4,
        )
        text = response.choices[0].message.content.strip()
        logger.info("AI response (%d chars): %s...", len(text), text[:60])
        return text
    except Exception as exc:
        logger.error("OpenAI API call failed: %s", exc)
        return None
