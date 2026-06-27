"""
Translation service for USSD menus.

Strategy (in priority order):
  1. Look up the string in the built-in TRANSLATIONS dictionary.
  2. If not found and OpenAI key is configured, call OpenAI to translate.
  3. Fall back to the English original.

All translations are cached in-process (Django cache) to avoid
repeated API calls for the same string + language pair.
"""
import hashlib
import logging

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ #
# Supported languages                                                  #
# ------------------------------------------------------------------ #

SUPPORTED_LANGUAGES: dict[str, str] = {
    'en': 'English',
    'sw': 'Kiswahili',
    'lg': 'Luganda',
    'rn': 'Runyankole',
}

DEFAULT_LANGUAGE = 'en'

# ------------------------------------------------------------------ #
# Built-in translation dictionary                                      #
# ------------------------------------------------------------------ #
# Keys are English strings; values are dicts keyed by language code.
# Add new strings here as the app grows.

TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── Language selection ──────────────────────────────────────────
    "Welcome to Farmer's Companion\nChoose language:": {
        'sw': "Karibu Farmer's Companion\nChagua lugha:",
        'lg': "Tukwanulirwa mu Farmer's Companion\nSalira olulimi:",
        'rn': "Murakaza neza kuri Farmer's Companion\nHura ururimi:",
    },
    "1. English": {
        'sw': '1. Kiingereza',
        'lg': '1. Olungereza',
        'rn': '1. Ikirundi',
    },
    "2. Kiswahili": {
        'sw': '2. Kiswahili',
        'lg': '2. Kiswahili',
        'rn': '2. Kiswahili',
    },
    "3. Luganda": {
        'sw': '3. Luganda',
        'lg': '3. Oluganda',
        'rn': '3. Oluganda',
    },
    "4. Runyankole": {
        'sw': '4. Runyankole',
        'lg': '4. Runyankole',
        'rn': '4. Runyankole',
    },

    # ── Main menu ───────────────────────────────────────────────────
    "Welcome to Farmer's Companion": {
        'sw': "Karibu kwenye Farmer's Companion",
        'lg': "Tukwanulirwa mu Farmer's Companion",
        'rn': "Murakaza neza kuri Farmer's Companion",
    },
    "1. Weather Forecast": {
        'sw': '1. Hali ya Hewa',
        'lg': '1. Obulagirizi bw\'omusana',
        'rn': '1. Amakuru y\'ikirere',
    },
    "2. Market Prices": {
        'sw': '2. Bei za Masoko',
        'lg': '2. Bbeeyi ez\'olusuku',
        'rn': '2. Ibiciro by\'amasoko',
    },
    "3. Crop Advisory": {
        'sw': '3. Ushauri wa Mazao',
        'lg': '3. Ebiragiro eby\'ebimera',
        'rn': '3. Inama z\'ubuhinzi',
    },
    "4. My Profile": {
        'sw': '4. Wasifu Wangu',
        'lg': '4. Porofayilo yange',
        'rn': '4. Umwirondoro wange',
    },
    "5. Change Language": {
        'sw': '5. Badilisha Lugha',
        'lg': '5. Kyusa olulimi',
        'rn': '5. Hindura ururimi',
    },
    "0. Exit": {
        'sw': '0. Toka',
        'lg': '0. Vamu',
        'rn': '0. Sohoka',
    },

    # ── Weather menu ────────────────────────────────────────────────
    "Weather Forecast": {
        'sw': 'Hali ya Hewa',
        'lg': 'Obulagirizi bw\'omusana',
        'rn': 'Amakuru y\'ikirere',
    },
    "1. Current weather (Kampala)": {
        'sw': '1. Hali ya hewa sasa (Kampala)',
        'lg': '1. Omusana kati (Kampala)',
        'rn': '1. Ikirere kino gihe (Kampala)',
    },
    "0. Back": {
        'sw': '0. Rudi',
        'lg': '0. Ddayo',
        'rn': '0. Garuka',
    },

    # ── Market prices menu ──────────────────────────────────────────
    "Market Prices": {
        'sw': 'Bei za Masoko',
        'lg': 'Bbeeyi ez\'olusuku',
        'rn': 'Ibiciro by\'amasoko',
    },
    "1. Maize": {
        'sw': '1. Mahindi',
        'lg': '1. Kasooli',
        'rn': '1. Kasooli',
    },
    "2. Wheat": {
        'sw': '2. Ngano',
        'lg': '2. Ngano',
        'rn': '2. Ingano',
    },
    "3. Tomatoes": {
        'sw': '3. Nyanya',
        'lg': '3. Enyanya',
        'rn': '3. Enyanya',
    },

    # ── Crop advisory menu ──────────────────────────────────────────
    "Crop Advisory": {
        'sw': 'Ushauri wa Mazao',
        'lg': 'Ebiragiro eby\'ebimera',
        'rn': 'Inama z\'ubuhinzi',
    },
    "1. Planting tips": {
        'sw': '1. Vidokezo vya kupanda',
        'lg': '1. Ebiragiro eby\'okusiga',
        'rn': '1. Inama zo gutera',
    },
    "2. Pest & disease alerts": {
        'sw': '2. Tahadhari za wadudu na magonjwa',
        'lg': '2. Obulamu bw\'endwadde n\'ensowera',
        'rn': '2. Amakuru y\'indwara n\'ibyounyi',
    },
    "3. Harvest advice": {
        'sw': '3. Ushauri wa mavuno',
        'lg': '3. Ebiragiro eby\'okuŋŋaba',
        'rn': '3. Inama zo gusarura',
    },

    # ── System messages ─────────────────────────────────────────────
    "Thank you for using Farmer's Companion. Goodbye!": {
        'sw': "Asante kwa kutumia Farmer's Companion. Kwaheri!",
        'lg': "Webale okukozesa Farmer's Companion. Weraba!",
        'rn': "Murakoze gukoresha Farmer's Companion. Murabeho!",
    },
    "Invalid option. Please try again.": {
        'sw': 'Chaguo batili. Tafadhali jaribu tena.',
        'lg': 'Okulonda okubi. Gezaako nate.',
        'rn': 'Amahitamo mabi. Ongera ugerageze.',
    },
    "Invalid choice. Please try again.": {
        'sw': 'Chaguo batili. Tafadhali jaribu tena.',
        'lg': 'Okulonda okubi. Gezaako nate.',
        'rn': 'Amahitamo mabi. Ongera ugerageze.',
    },
    "Could not retrieve weather right now. Try again later.": {
        'sw': 'Haikuweza kupata hali ya hewa sasa. Jaribu baadaye.',
        'lg': 'Tetusobodde kubona omulabirizi w\'omusana. Gezaako oluvannyuma.',
        'rn': 'Ntabwo twashoboye kuronka amakuru y\'ikirere. Gerageza nyuma.',
    },
    "You are not registered yet.\nSend REGISTER <name> via SMS\nor visit our website to sign up.": {
        'sw': 'Bado hujasajiliwa.\nTuma REGISTER <jina> kwa SMS\nau tembelea tovuti yetu.',
        'lg': 'Tonnateeka nnawe.\nTuma REGISTER <erinnya> mu SMS\noba laba website yaffe.',
        'rn': 'Ntabwo wanditse.\nHereza REGISTER <izina> kuri SMS\ncyangwa sura website yacu.',
    },
}

# Cache TTL: 24 hours
_CACHE_TTL = 86_400


# ------------------------------------------------------------------ #
# Public API                                                           #
# ------------------------------------------------------------------ #

def translate(text: str, language: str) -> str:
    """
    Translate *text* into *language*.
    Returns the original English text if translation is unavailable.
    """
    if language == DEFAULT_LANGUAGE or language not in SUPPORTED_LANGUAGES:
        return text

    # 1. Check in-process cache
    cache_key = _cache_key(text, language)
    cached = cache.get(cache_key)
    if cached:
        return cached

    # 2. Built-in dictionary
    result = TRANSLATIONS.get(text, {}).get(language)
    if result:
        cache.set(cache_key, result, _CACHE_TTL)
        return result

    # 3. OpenAI fallback
    result = _openai_translate(text, language)
    if result:
        cache.set(cache_key, result, _CACHE_TTL)
        return result

    # 4. English fallback
    logger.warning("No translation found for lang=%s text='%s...', using English", language, text[:40])
    return text


def get_menu(lines: list[str], language: str, prefix: str = 'CON') -> str:
    """
    Build a USSD menu string from a list of lines, translating each line.
    prefix is 'CON' (continue session) or 'END' (close session).
    """
    translated = [translate(line, language) for line in lines]
    return prefix + ' ' + '\n'.join(translated)


# ------------------------------------------------------------------ #
# Internal helpers                                                     #
# ------------------------------------------------------------------ #

def _cache_key(text: str, language: str) -> str:
    digest = hashlib.md5(text.encode()).hexdigest()[:12]
    return f"ussd_trans_{language}_{digest}"


def _openai_translate(text: str, language: str) -> str | None:
    """Call OpenAI to translate text. Returns None on any failure."""
    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        return None
    try:
        import openai
        openai.api_key = api_key
        lang_name = SUPPORTED_LANGUAGES[language]
        response = openai.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    'role': 'system',
                    'content': (
                        f'You are a translator. Translate the following USSD menu text '
                        f'to {lang_name}. Preserve newlines and numbering exactly. '
                        f'Return only the translated text, nothing else.'
                    ),
                },
                {'role': 'user', 'content': text},
            ],
            max_tokens=300,
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("OpenAI translation failed: %s", exc)
        return None
