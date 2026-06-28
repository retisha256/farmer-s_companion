"""
Voice menu XML builders for Africa's Talking ActionScript.

Africa's Talking voice ActionScript reference:
  <Say>          — text-to-speech
  <GetDigits>    — collect DTMF keypad input, POST result to callbackUrl
  <Record>       — record caller's voice
  <Dial>         — connect to another number
  <Hangup>       — end the call
  <Redirect>     — hand off to another URL

Each function returns a complete XML string ready to send back to AT.
"""
from django.conf import settings


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def _xml(body: str) -> str:
    """Wrap content in the root <Response> element."""
    return f'<?xml version="1.0" encoding="UTF-8"?><Response>{body}</Response>'


def _say(text: str, voice: str = 'woman', playBeep: bool = False) -> str:
    """Return a <Say> element."""
    beep = ' playBeep="true"' if playBeep else ''
    return f'<Say voice="{voice}"{beep}>{text}</Say>'


def _get_digits(
    say_text: str,
    callback_url: str,
    num_digits: int = 1,
    timeout: int = 30,
    finish_on_key: str = '#',
    voice: str = 'woman',
) -> str:
    """Return a <GetDigits> element with embedded <Say>."""
    return (
        f'<GetDigits numDigits="{num_digits}" timeout="{timeout}" '
        f'finishOnKey="{finish_on_key}" callbackUrl="{callback_url}">'
        f'{_say(say_text, voice)}'
        f'</GetDigits>'
    )


def _callback_url(path: str) -> str:
    """Build an absolute callback URL using the ngrok/server base."""
    # Use the first non-localhost host from ALLOWED_HOSTS as the base
    base = next(
        (h for h in settings.ALLOWED_HOSTS if h not in ('localhost', '127.0.0.1', '*')),
        '127.0.0.1:8000',
    )
    scheme = 'https' if '.' in base else 'http'
    return f'{scheme}://{base}{path}'


# ------------------------------------------------------------------ #
# Menu screens                                                         #
# ------------------------------------------------------------------ #

LANGUAGE_NAMES = {
    'en': 'English',
    'sw': 'Kiswahili',
    'lg': 'Luganda',
    'rn': 'Runyankole',
    'ac': 'Acholi',
}

# Language-specific greetings spoken by TTS
GREETINGS = {
    'en': "Welcome to Farmer's Companion.",
    'sw': "Karibu Farmer's Companion.",
    'lg': "Tukwanulirwa mu Farmer's Companion.",
    'rn': "Murakaza neza kuri Farmer's Companion.",
    'ac': "Wubone i Farmer's Companion.",
}

MAIN_MENU_TEXT = {
    'en': (
        "Press 1 for Weather. "
        "Press 2 for Market Prices. "
        "Press 3 for Pest Diagnosis. "
        "Press 4 for Farming Tips. "
        "Press 5 for AI Advice. "
        "Press 7 to Change Language. "
        "Press 0 to Exit."
    ),
    'sw': (
        "Bonyeza 1 kwa Hali ya Hewa. "
        "Bonyeza 2 kwa Bei za Masoko. "
        "Bonyeza 3 kwa Utambuzi wa Wadudu. "
        "Bonyeza 4 kwa Vidokezo vya Kilimo. "
        "Bonyeza 5 kwa Ushauri wa AI. "
        "Bonyeza 7 kubadilisha Lugha. "
        "Bonyeza 0 kutoka."
    ),
    'lg': (
        "Nyiga 1 ku Obulagirizi bw'omusana. "
        "Nyiga 2 ku Bbeeyi ez'olusuku. "
        "Nyiga 3 ku Endwadde y'ebimera. "
        "Nyiga 4 ku Ebiragiro eby'obulimi. "
        "Nyiga 5 ku Ebiragiro bya AI. "
        "Nyiga 7 okukyusa olulimi. "
        "Nyiga 0 okuvamu."
    ),
    'rn': (
        "Kanda 1 kuri Amakuru y'ikirere. "
        "Kanda 2 kuri Ibiciro by'amasoko. "
        "Kanda 3 kuri Indwara z'ubuhinzi. "
        "Kanda 4 kuri Inama z'ubuhinzi. "
        "Kanda 5 kuri Inama za AI. "
        "Kanda 7 guhindura ururimi. "
        "Kanda 0 gusohoka."
    ),
    'ac': (
        "Ket 1 pi Cik me Cua. "
        "Ket 2 pi Wel pa Cen. "
        "Ket 3 pi Temo pa Kongo. "
        "Ket 4 pi Pwony pa Jami. "
        "Ket 5 pi Lok pa AI. "
        "Ket 7 loko leb. "
        "Ket 0 wot."
    ),
}

WEATHER_MENU_TEXT = {
    'en': "Press 1 for today's weather. Press 2 for a 7-day forecast. Press 0 to go back.",
    'sw': "Bonyeza 1 kwa hali ya hewa leo. Bonyeza 2 kwa utabiri wa siku 7. Bonyeza 0 kurudi.",
    'lg': "Nyiga 1 ku omusana wa leero. Nyiga 2 ku obulagirizi bwa naku 7. Nyiga 0 okuddayo.",
    'rn': "Kanda 1 kuri ikirere k'uyu munsi. Kanda 2 kuri amakuru ya iminsi 7. Kanda 0 gusubira.",
    'ac': "Ket 1 pi cua wa tin. Ket 2 pi cik me nino abiro. Ket 0 dok.",
}

MARKET_MENU_TEXT = {
    'en': "Press 1 for Maize. Press 2 for Beans. Press 3 for Cassava. Press 4 for Coffee. Press 0 to go back.",
    'sw': "Bonyeza 1 kwa Mahindi. Bonyeza 2 kwa Maharagwe. Bonyeza 3 kwa Muhogo. Bonyeza 4 kwa Kahawa. Bonyeza 0 kurudi.",
    'lg': "Nyiga 1 ku Kasooli. Nyiga 2 ku Ebijanjaalo. Nyiga 3 ku Muwogo. Nyiga 4 ku Kawuufu. Nyiga 0 okuddayo.",
    'rn': "Kanda 1 kuri Kasooli. Kanda 2 kuri Ibishyimbo. Kanda 3 kuri Imyumbati. Kanda 4 kuri Ikawa. Kanda 0 gusubira.",
    'ac': "Ket 1 pi Kal. Ket 2 pi Latooma. Ket 3 pi Bao. Ket 4 pi Kawa. Ket 0 dok.",
}

PEST_MENU_TEXT = {
    'en': "Press 1 for yellow or wilting leaves. Press 2 for holes in leaves. Press 3 for stunted growth. Press 0 to go back.",
    'sw': "Bonyeza 1 kwa majani ya njano. Bonyeza 2 kwa mashimo kwenye majani. Bonyeza 3 kwa ukuaji mdogo. Bonyeza 0 kurudi.",
    'lg': "Nyiga 1 ku ebijanjalo ebirutirutira. Nyiga 2 ku embuzi mu ebijanjalo. Nyiga 3 ku enkula ennono. Nyiga 0 okuddayo.",
    'rn': "Kanda 1 kuri amababi y'umuhondo. Kanda 2 kuri imyobo mu mababi. Kanda 3 kuri kwiyongera guke. Kanda 0 gusubira.",
    'ac': "Ket 1 pi pot maleng. Ket 2 pi bal i pot. Ket 3 pi nen matidi. Ket 0 dok.",
}

AI_MENU_TEXT = {
    'en': "Press 1 for crop advice. Press 2 for soil tips. Press 3 for fertilizer guide. Press 4 for irrigation tips. Press 0 to go back.",
    'sw': "Bonyeza 1 kwa ushauri wa mazao. Bonyeza 2 kwa vidokezo vya udongo. Bonyeza 3 kwa mwongozo wa mbolea. Bonyeza 4 kwa umwagiliaji. Bonyeza 0 kurudi.",
    'lg': "Nyiga 1 ku ebiragiro eby'ebimera. Nyiga 2 ku ttaka. Nyiga 3 ku bbombo. Nyiga 4 ku nsuuzi. Nyiga 0 okuddayo.",
    'rn': "Kanda 1 kuri ibihingwa. Kanda 2 kuri ubutaka. Kanda 3 kuri ifumbire. Kanda 4 kuri amazi. Kanda 0 gusubira.",
    'ac': "Ket 1 pi cek. Ket 2 pi ngom. Ket 3 pi mwolo. Ket 4 pi pi. Ket 0 dok.",
}

LANGUAGE_MENU_TEXT = (
    "Press 1 for English. "
    "Press 2 for Kiswahili. "
    "Press 3 for Luganda. "
    "Press 4 for Runyankole. "
    "Press 5 for Acholi."
)

GOODBYE_TEXT = {
    'en': "Thank you for calling Farmer's Companion. Goodbye!",
    'sw': "Asante kwa kupiga simu Farmer's Companion. Kwaheri!",
    'lg': "Webale okukuba essimu Farmer's Companion. Weraba!",
    'rn': "Murakoze guhamagara Farmer's Companion. Murabeho!",
    'ac': "Apwoyo pi lwoyo Farmer's Companion. Wot Maber!",
}


# ------------------------------------------------------------------ #
# Public menu builders                                                 #
# ------------------------------------------------------------------ #

def language_selection_xml() -> str:
    """Step 0: ask caller to choose a language."""
    text = (
        "Welcome to Farmer's Companion. "
        + LANGUAGE_MENU_TEXT
    )
    return _xml(_get_digits(text, _callback_url('/voice/callback/')))


def main_menu_xml(lang: str = 'en') -> str:
    greeting = GREETINGS.get(lang, GREETINGS['en'])
    menu = MAIN_MENU_TEXT.get(lang, MAIN_MENU_TEXT['en'])
    return _xml(_get_digits(
        f"{greeting} {menu}",
        _callback_url('/voice/callback/'),
    ))


def weather_menu_xml(lang: str = 'en') -> str:
    text = WEATHER_MENU_TEXT.get(lang, WEATHER_MENU_TEXT['en'])
    return _xml(_get_digits(text, _callback_url('/voice/callback/')))


def market_menu_xml(lang: str = 'en') -> str:
    text = MARKET_MENU_TEXT.get(lang, MARKET_MENU_TEXT['en'])
    return _xml(_get_digits(text, _callback_url('/voice/callback/')))


def pest_menu_xml(lang: str = 'en') -> str:
    text = PEST_MENU_TEXT.get(lang, PEST_MENU_TEXT['en'])
    return _xml(_get_digits(text, _callback_url('/voice/callback/')))


def ai_menu_xml(lang: str = 'en') -> str:
    text = AI_MENU_TEXT.get(lang, AI_MENU_TEXT['en'])
    return _xml(_get_digits(text, _callback_url('/voice/callback/')))


def speak_and_return_xml(message: str, return_menu_xml: str) -> str:
    """Speak a message then show another menu."""
    # AT processes <Say> first, then <GetDigits> from the next element
    # We embed both in the response — the menu XML's inner content
    # replaces the outer wrapper so we concatenate the inner body.
    inner = _say(message) + return_menu_xml.replace(
        '<?xml version="1.0" encoding="UTF-8"?><Response>', ''
    ).replace('</Response>', '')
    return _xml(inner)


def speak_and_hangup_xml(message: str) -> str:
    """Speak a message and end the call."""
    return _xml(_say(message) + '<Hangup/>')
