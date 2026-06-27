"""
USSD menu builders.

Every menu function accepts a `language` code and returns a fully
translated CON/END string ready to send back to Africa's Talking.
"""
from .translations import get_menu, translate


# ------------------------------------------------------------------ #
# Language selection (Step 0 — always in English)                     #
# ------------------------------------------------------------------ #

def language_menu() -> str:
    """Always shown in English — the user hasn't chosen a language yet."""
    return (
        "CON Welcome to Farmer's Companion\n"
        "Choose language:\n"
        "1. English\n"
        "2. Kiswahili\n"
        "3. Luganda\n"
        "4. Runyankole\n"
        "5. Acholi"
    )


# Map digit → language code  (step 0 of every session)
LANGUAGE_MAP: dict[str, str] = {
    '1': 'en',
    '2': 'sw',
    '3': 'lg',
    '4': 'rn',
    '5': 'ac',
}


# ------------------------------------------------------------------ #
# Main menu (7 options)                                               #
# ------------------------------------------------------------------ #

def main_menu(language: str = 'en') -> str:
    return get_menu([
        "Welcome to Farmer's Companion",
        "1. Weather Forecast",
        "2. Market Prices",
        "3. Pest Diagnosis",
        "4. Farming Tips",
        "5. Ask AI",
        "6. My Profile",
        "7. Change Language",
        "0. Exit",
    ], language)


# ------------------------------------------------------------------ #
# Sub-menus                                                            #
# ------------------------------------------------------------------ #

def weather_menu(language: str = 'en') -> str:
    return get_menu([
        "Weather Forecast",
        "1. Today's weather",
        "2. 7-day forecast",
        "0. Back",
    ], language)


def market_menu(language: str = 'en') -> str:
    return get_menu([
        "Market Prices",
        "1. Maize",
        "2. Beans",
        "3. Cassava",
        "4. Coffee",
        "0. Back",
    ], language)


def pest_menu(language: str = 'en') -> str:
    return get_menu([
        "Pest Diagnosis",
        "Describe your crop problem:",
        "1. Yellow/wilting leaves",
        "2. Holes in leaves",
        "3. Stunted growth",
        "4. Other (describe)",
        "0. Back",
    ], language)


def farming_tips_menu(language: str = 'en') -> str:
    return get_menu([
        "Farming Tips",
        "1. Planting tips",
        "2. Pest & disease alerts",
        "3. Harvest advice",
        "0. Back",
    ], language)


def ai_menu(language: str = 'en') -> str:
    return get_menu([
        "Ask AI",
        "1. Crop advice",
        "2. Soil tips",
        "3. Fertilizer guide",
        "4. Irrigation tips",
        "0. Back",
    ], language)


# ------------------------------------------------------------------ #
# Helper                                                               #
# ------------------------------------------------------------------ #

def end_msg(text: str, language: str = 'en') -> str:
    """Wrap a translatable message as an END response."""
    return 'END ' + translate(text, language)
