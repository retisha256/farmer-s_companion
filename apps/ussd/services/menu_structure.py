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
    """Always shown in English — user hasn't chosen a language yet."""
    return (
        "CON Welcome to Farmer's Companion\n"
        "Choose language:\n"
        "1. English\n"
        "2. Kiswahili\n"
        "3. Luganda\n"
        "4. Runyankole"
    )


# Map numeric choice → language code
LANGUAGE_MAP: dict[str, str] = {
    '1': 'en',
    '2': 'sw',
    '3': 'lg',
    '4': 'rn',
}


# ------------------------------------------------------------------ #
# Main menu                                                            #
# ------------------------------------------------------------------ #

def main_menu(language: str = 'en') -> str:
    return get_menu([
        "Welcome to Farmer's Companion",
        "1. Weather Forecast",
        "2. Market Prices",
        "3. Crop Advisory",
        "4. My Profile",
        "5. Change Language",
        "0. Exit",
    ], language)


# ------------------------------------------------------------------ #
# Sub-menus                                                            #
# ------------------------------------------------------------------ #

def weather_menu(language: str = 'en') -> str:
    return get_menu([
        "Weather Forecast",
        "1. Current weather (Kampala)",
        "0. Back",
    ], language)


def market_menu(language: str = 'en') -> str:
    return get_menu([
        "Market Prices",
        "1. Maize",
        "2. Wheat",
        "3. Tomatoes",
        "0. Back",
    ], language)


def crop_menu(language: str = 'en') -> str:
    return get_menu([
        "Crop Advisory",
        "1. Planting tips",
        "2. Pest & disease alerts",
        "3. Harvest advice",
        "0. Back",
    ], language)


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #

def end_msg(text: str, language: str = 'en') -> str:
    """Wrap a translatable message as an END response."""
    return 'END ' + translate(text, language)
