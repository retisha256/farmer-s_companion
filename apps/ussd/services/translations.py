"""
Translation service for USSD menus.

Strategy (priority order):
  1. Django cache (24h TTL)
  2. Built-in TRANSLATIONS dictionary  ← fast, zero API cost
  3. OpenAI gpt-3.5-turbo              ← dynamic fallback
  4. English original                  ← always safe

Supported languages: en, sw (Kiswahili), lg (Luganda),
                     rn (Runyankole), ac (Acholi)
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
    'ac': 'Acholi',
}

DEFAULT_LANGUAGE = 'en'
_CACHE_TTL = 86_400   # 24 hours

# ------------------------------------------------------------------ #
# Built-in translation dictionary                                      #
# ------------------------------------------------------------------ #

TRANSLATIONS: dict[str, dict[str, str]] = {

    # ── Language selection (always shown in English) ────────────────
    "Welcome to Farmer's Companion\nChoose language:": {
        'sw': "Karibu Farmer's Companion\nChagua lugha:",
        'lg': "Tukwanulirwa mu Farmer's Companion\nSalira olulimi:",
        'rn': "Murakaza neza kuri Farmer's Companion\nHura ururimi:",
        'ac': "Wubone i Farmer's Companion\nYer leb:",
    },
    "1. English": {
        'sw': '1. Kiingereza', 'lg': '1. Olungereza',
        'rn': '1. Ikirundi',   'ac': '1. Ingiriza',
    },
    "2. Kiswahili": {
        'sw': '2. Kiswahili', 'lg': '2. Kiswahili',
        'rn': '2. Kiswahili', 'ac': '2. Kiswahili',
    },
    "3. Luganda": {
        'sw': '3. Luganda', 'lg': '3. Oluganda',
        'rn': '3. Oluganda', 'ac': '3. Luganda',
    },
    "4. Runyankole": {
        'sw': '4. Runyankole', 'lg': '4. Runyankole',
        'rn': '4. Runyankole', 'ac': '4. Runyankole',
    },
    "5. Acholi": {
        'sw': '5. Acholi', 'lg': '5. Acholi',
        'rn': '5. Acholi', 'ac': '5. Leb Acholi',
    },

    # ── Main menu ───────────────────────────────────────────────────
    "Welcome to Farmer's Companion": {
        'sw': "Karibu kwenye Farmer's Companion",
        'lg': "Tukwanulirwa mu Farmer's Companion",
        'rn': "Murakaza neza kuri Farmer's Companion",
        'ac': "Wubone i Farmer's Companion",
    },
    "1. Weather Forecast": {
        'sw': '1. Hali ya Hewa',
        'lg': "1. Obulagirizi bw'omusana",
        'rn': "1. Amakuru y'ikirere",
        'ac': '1. Cik me Cua',
    },
    "2. Market Prices": {
        'sw': '2. Bei za Masoko',
        'lg': "2. Bbeeyi ez'olusuku",
        'rn': "2. Ibiciro by'amasoko",
        'ac': '2. Wel pa Cen',
    },
    "3. Pest Diagnosis": {
        'sw': '3. Utambuzi wa Wadudu',
        'lg': "3. Endwadde y'ebimera",
        'rn': "3. Indwara z'ubuhinzi",
        'ac': '3. Temo pa Kongo',
    },
    "4. Farming Tips": {
        'sw': '4. Vidokezo vya Kilimo',
        'lg': "4. Ebiragiro eby'obulimi",
        'rn': "4. Inama z'ubuhinzi",
        'ac': '4. Pwony pa Jami',
    },
    "5. Ask AI": {
        'sw': '5. Uliza AI',
        'lg': '5. Buuza AI',
        'rn': '5. Baza AI',
        'ac': '5. Penyo AI',
    },
    "6. My Profile": {
        'sw': '6. Wasifu Wangu',
        'lg': '6. Porofayilo yange',
        'rn': '6. Umwirondoro wange',
        'ac': '6. Aketa pa An',
    },
    "7. Change Language": {
        'sw': '7. Badilisha Lugha',
        'lg': '7. Kyusa olulimi',
        'rn': '7. Hindura ururimi',
        'ac': '7. Loko Leb',
    },
    "0. Exit": {
        'sw': '0. Toka',   'lg': '0. Vamu',
        'rn': '0. Sohoka', 'ac': '0. Wot',
    },

    # ── Weather ─────────────────────────────────────────────────────
    "Weather Forecast": {
        'sw': 'Hali ya Hewa',
        'lg': "Obulagirizi bw'omusana",
        'rn': "Amakuru y'ikirere",
        'ac': 'Cik me Cua',
    },
    "1. Today's weather": {
        'sw': "1. Hali ya hewa leo",
        'lg': "1. Omusana wa leero",
        'rn': "1. Ikirere k'uyu munsi",
        'ac': '1. Cua wa Tin',
    },
    "2. 7-day forecast": {
        'sw': '2. Utabiri wa siku 7',
        'lg': '2. Obulagirizi bwa naku 7',
        'rn': '2. Amakuru ya iminsi 7',
        'ac': '2. Cik me Nino Abiro',
    },
    "0. Back": {
        'sw': '0. Rudi', 'lg': '0. Ddayo',
        'rn': '0. Garuka', 'ac': '0. Dok',
    },

    # ── Market prices ───────────────────────────────────────────────
    "Market Prices": {
        'sw': 'Bei za Masoko',
        'lg': "Bbeeyi ez'olusuku",
        'rn': "Ibiciro by'amasoko",
        'ac': 'Wel pa Cen',
    },
    "1. Maize": {
        'sw': '1. Mahindi', 'lg': '1. Kasooli',
        'rn': '1. Kasooli', 'ac': '1. Kal',
    },
    "2. Beans": {
        'sw': '2. Maharagwe', 'lg': '2. Ebijanjaalo',
        'rn': '2. Ibishyimbo', 'ac': '2. Latooma',
    },
    "3. Cassava": {
        'sw': '3. Muhogo', 'lg': '3. Muwogo',
        'rn': '3. Imyumbati', 'ac': '3. Bao',
    },
    "4. Coffee": {
        'sw': '4. Kahawa', 'lg': '4. Kawuufu',
        'rn': '4. Ikawa', 'ac': '4. Kawa',
    },

    # ── Pest diagnosis ──────────────────────────────────────────────
    "Pest Diagnosis": {
        'sw': 'Utambuzi wa Wadudu',
        'lg': "Endwadde y'ebimera",
        'rn': "Indwara z'ubuhinzi",
        'ac': 'Temo pa Kongo',
    },
    "Describe your crop problem:": {
        'sw': 'Elezea tatizo la zao lako:',
        'lg': "Nnyonnyola obuzibu bw'ekimera kyo:",
        'rn': "Sobanura ikibazo cy'igihingwa cyawe:",
        'ac': 'Nyut can pa cek megi:',
    },
    "1. Yellow/wilting leaves": {
        'sw': '1. Majani ya njano/yanayoanguka',
        'lg': '1. Ebijanjalo ebirutirutira/ebikwansa',
        'rn': '1. Amababi y\'umuhondo/agadindira',
        'ac': '1. Pot maleng/ma golo',
    },
    "2. Holes in leaves": {
        'sw': '2. Mashimo kwenye majani',
        'lg': '2. Embuzi mu ebijanjalo',
        'rn': '2. Imy구멍 mu mababi',
        'ac': '2. Bal i pot',
    },
    "3. Stunted growth": {
        'sw': '3. Ukuaji uliosimama',
        'lg': '3. Enkula ennono',
        'rn': '3. Kwiyongera guke',
        'ac': '3. Nen matidi',
    },
    "4. Other (describe)": {
        'sw': '4. Nyingine (elezea)',
        'lg': '4. Ekirala (nnyonnyola)',
        'rn': '4. Ikindi (sobanura)',
        'ac': '4. Mukene (nyut)',
    },

    # ── Ask AI ──────────────────────────────────────────────────────
    "Ask AI": {
        'sw': 'Uliza AI',    'lg': 'Buuza AI',
        'rn': 'Baza AI',     'ac': 'Penyo AI',
    },
    "1. Crop advice": {
        'sw': '1. Ushauri wa mazao',
        'lg': "1. Ebiragiro eby'ebimera",
        'rn': "1. Inama z'ibihingwa",
        'ac': '1. Pwony pa Cek',
    },
    "2. Soil tips": {
        'sw': '2. Vidokezo vya udongo',
        'lg': '2. Ebiragiro ku ttaka',
        'rn': '2. Inama ku butaka',
        'ac': '2. Pwony pa Ngom',
    },
    "3. Fertilizer guide": {
        'sw': '3. Mwongozo wa mbolea',
        'lg': '3. Ebiragiro ku bbombo',
        'rn': '3. Inama ku ifumbire',
        'ac': '3. Pwony pa Mwolo',
    },
    "4. Irrigation tips": {
        'sw': '4. Vidokezo vya umwagiliaji',
        'lg': '4. Ebiragiro ku nsuuzi',
        'rn': '4. Inama ku kuhira amazi',
        'ac': '4. Pwony pa Pi',
    },

    # ── Farming tips ────────────────────────────────────────────────
    "Farming Tips": {
        'sw': 'Vidokezo vya Kilimo',
        'lg': "Ebiragiro eby'obulimi",
        'rn': "Inama z'ubuhinzi",
        'ac': 'Pwony pa Jami',
    },
    "1. Planting tips": {
        'sw': '1. Vidokezo vya kupanda',
        'lg': "1. Ebiragiro eby'okusiga",
        'rn': '1. Inama zo gutera',
        'ac': '1. Pwony pa Cibo Cek',
    },
    "2. Pest & disease alerts": {
        'sw': '2. Tahadhari za wadudu na magonjwa',
        'lg': "2. Obulamu bw'endwadde n'ensowera",
        'rn': "2. Amakuru y'indwara n'ibyounyi",
        'ac': '2. Lok pa Kite ki Two',
    },
    "3. Harvest advice": {
        'sw': '3. Ushauri wa mavuno',
        'lg': "3. Ebiragiro eby'okuŋŋaba",
        'rn': '3. Inama zo gusarura',
        'ac': '3. Pwony pa Kayo Cek',
    },

    # ── System messages ─────────────────────────────────────────────
    "Thank you for using Farmer's Companion. Goodbye!": {
        'sw': "Asante kwa kutumia Farmer's Companion. Kwaheri!",
        'lg': "Webale okukozesa Farmer's Companion. Weraba!",
        'rn': "Murakoze gukoresha Farmer's Companion. Murabeho!",
        'ac': "Apwoyo pi tiyo ki Farmer's Companion. Wot Maber!",
    },
    "Invalid option. Please try again.": {
        'sw': 'Chaguo batili. Tafadhali jaribu tena.',
        'lg': 'Okulonda okubi. Gezaako nate.',
        'rn': 'Amahitamo mabi. Ongera ugerageze.',
        'ac': 'Yero maber. Tem doki.',
    },
    "Invalid choice. Please try again.": {
        'sw': 'Chaguo batili. Tafadhali jaribu tena.',
        'lg': 'Okulonda okubi. Gezaako nate.',
        'rn': 'Amahitamo mabi. Ongera ugerageze.',
        'ac': 'Yero maber. Tem doki.',
    },
    "Could not retrieve weather right now. Try again later.": {
        'sw': 'Haikuweza kupata hali ya hewa sasa. Jaribu baadaye.',
        'lg': "Tetusobodde kubona omulabirizi w'omusana. Gezaako oluvannyuma.",
        'rn': "Ntabwo twashoboye kuronka amakuru y'ikirere. Gerageza nyuma.",
        'ac': 'Peke twero nongo cik pa cua kina. Tem lacen.',
    },
    "You are not registered yet.\nSend REGISTER <name> via SMS\nor visit our website to sign up.": {
        'sw': 'Bado hujasajiliwa.\nTuma REGISTER <jina> kwa SMS\nau tembelea tovuti yetu.',
        'lg': 'Tonnateeka nnawe.\nTuma REGISTER <erinnya> mu SMS\noba laba website yaffe.',
        'rn': 'Ntabwo wanditse.\nHereza REGISTER <izina> kuri SMS\ncyangwa sura website yacu.',
        'ac': 'Peke icoyo nyiŋ ducu.\nCwal REGISTER <nyiŋ> pi SMS\nkadi lim website waŋwa.',
    },
    "AI service is unavailable. Try again later.": {
        'sw': 'Huduma ya AI haipo. Jaribu baadaye.',
        'lg': 'Obuweereza bwa AI tebulipo. Gezaako oluvannyuma.',
        'rn': 'Serivisi ya AI ntiboneka. Gerageza nyuma.',
        'ac': 'Tic pa AI pe tye. Tem lacen.',
    },
}


# ------------------------------------------------------------------ #
# Public API                                                           #
# ------------------------------------------------------------------ #

def translate(text: str, language: str) -> str:
    """
    Translate *text* into *language*.
    Falls back to the English original if no translation is found.
    """
    if language == DEFAULT_LANGUAGE or language not in SUPPORTED_LANGUAGES:
        return text

    cache_key = _cache_key(text, language)
    cached = cache.get(cache_key)
    if cached:
        return cached

    # Built-in dictionary
    result = TRANSLATIONS.get(text, {}).get(language)
    if result:
        cache.set(cache_key, result, _CACHE_TTL)
        return result

    # OpenAI fallback
    result = _openai_translate(text, language)
    if result:
        cache.set(cache_key, result, _CACHE_TTL)
        return result

    logger.warning("No translation for lang=%s text='%.40s', using English", language, text)
    return text


def get_menu(lines: list[str], language: str, prefix: str = 'CON') -> str:
    """
    Build a USSD menu string from a list of lines, translating each one.
    prefix is 'CON' (keep session open) or 'END' (close session).
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
        client = openai.OpenAI(api_key=api_key)
        lang_name = SUPPORTED_LANGUAGES[language]
        response = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    'role': 'system',
                    'content': (
                        f'You are a translator for a farmer USSD app in Uganda. '
                        f'Translate the following text to {lang_name}. '
                        f'Preserve all newlines and numbering exactly as given. '
                        f'Return only the translated text — no explanations.'
                    ),
                },
                {'role': 'user', 'content': text},
            ],
            max_tokens=300,
            temperature=0.1,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("OpenAI translation failed: %s", exc)
        return None
