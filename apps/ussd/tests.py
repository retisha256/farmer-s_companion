"""
Tests for the upgraded USSD flow:
  - 5-language selection (EN/SW/LG/RN/AC)
  - 7-option main menu
  - Weather, market prices, pest diagnosis, farming tips, Ask AI
  - UserLanguagePreference model
  - Translation service
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client

from apps.ussd.models import UserLanguagePreference
from apps.ussd.services.ussd_handler import handle_ussd_request
from apps.ussd.services.translations import translate, get_menu, SUPPORTED_LANGUAGES
from apps.ussd.services.menu_structure import LANGUAGE_MAP


PHONE = '+256701066872'
SESSION = 'test-session-001'


def req(text, phone=PHONE, session=SESSION):
    return handle_ussd_request(session, phone, text)


# ─────────────────────────────────────────────────────────────────── #
# Translation service                                                  #
# ─────────────────────────────────────────────────────────────────── #

class TranslationServiceTest(TestCase):

    def test_english_unchanged(self):
        self.assertEqual(translate("0. Exit", 'en'), "0. Exit")

    def test_kiswahili_exit(self):
        self.assertEqual(translate("0. Exit", 'sw'), '0. Toka')

    def test_luganda_exit(self):
        self.assertEqual(translate("0. Exit", 'lg'), '0. Vamu')

    def test_runyankole_exit(self):
        self.assertEqual(translate("0. Exit", 'rn'), '0. Sohoka')

    def test_acholi_exit(self):
        self.assertEqual(translate("0. Exit", 'ac'), '0. Wot')

    def test_unknown_language_falls_back_to_english(self):
        self.assertEqual(translate("0. Exit", 'xx'), "0. Exit")

    def test_missing_key_returns_original(self):
        with patch('apps.ussd.services.translations._openai_translate', return_value=None):
            result = translate("Some unknown string xyz", 'sw')
        self.assertEqual(result, "Some unknown string xyz")

    def test_get_menu_english_prefix(self):
        menu = get_menu(["Market Prices", "1. Maize"], 'en')
        self.assertTrue(menu.startswith('CON '))
        self.assertIn('Market Prices', menu)

    def test_get_menu_kiswahili(self):
        menu = get_menu(["Market Prices", "1. Maize"], 'sw')
        self.assertIn('Bei za Masoko', menu)
        self.assertIn('Mahindi', menu)

    def test_get_menu_acholi(self):
        menu = get_menu(["Market Prices"], 'ac')
        self.assertIn('Wel pa Cen', menu)

    def test_get_menu_end_prefix(self):
        menu = get_menu(["Done"], 'en', prefix='END')
        self.assertTrue(menu.startswith('END '))

    def test_five_languages_supported(self):
        for code in ('en', 'sw', 'lg', 'rn', 'ac'):
            self.assertIn(code, SUPPORTED_LANGUAGES)


# ─────────────────────────────────────────────────────────────────── #
# UserLanguagePreference model                                         #
# ─────────────────────────────────────────────────────────────────── #

class UserLanguagePreferenceTest(TestCase):

    def test_default_is_english(self):
        self.assertEqual(UserLanguagePreference.get_language('+256700000001'), 'en')

    def test_set_and_get(self):
        UserLanguagePreference.set_language('+256700000001', 'sw')
        self.assertEqual(UserLanguagePreference.get_language('+256700000001'), 'sw')

    def test_update_existing(self):
        UserLanguagePreference.set_language('+256700000002', 'sw')
        UserLanguagePreference.set_language('+256700000002', 'ac')
        self.assertEqual(UserLanguagePreference.get_language('+256700000002'), 'ac')

    def test_acholi_choice_stored(self):
        UserLanguagePreference.set_language(PHONE, 'ac')
        self.assertEqual(UserLanguagePreference.get_language(PHONE), 'ac')

    def test_str(self):
        pref = UserLanguagePreference.objects.create(
            phone_number='+256700000003', preferred_language='rn')
        self.assertIn('Runyankole', str(pref))

    def test_language_map_has_five_entries(self):
        self.assertEqual(len(LANGUAGE_MAP), 5)
        self.assertEqual(LANGUAGE_MAP['5'], 'ac')


# ─────────────────────────────────────────────────────────────────── #
# USSD handler — language selection                                    #
# ─────────────────────────────────────────────────────────────────── #

class LanguageSelectionTest(TestCase):

    def test_new_user_sees_language_menu(self):
        r = req('')
        self.assertTrue(r.startswith('CON'))
        self.assertIn('Choose language', r)
        self.assertIn('Acholi', r)

    def test_returning_user_skips_language_menu(self):
        UserLanguagePreference.set_language(PHONE, 'sw')
        r = req('')
        self.assertIn('Hali ya Hewa', r)   # Kiswahili main menu

    def test_select_english(self):
        r = req('1')
        self.assertEqual(UserLanguagePreference.get_language(PHONE), 'en')
        self.assertIn('Weather Forecast', r)

    def test_select_kiswahili(self):
        r = req('2')
        self.assertEqual(UserLanguagePreference.get_language(PHONE), 'sw')
        self.assertIn('Hali ya Hewa', r)

    def test_select_luganda(self):
        r = req('3')
        self.assertEqual(UserLanguagePreference.get_language(PHONE), 'lg')

    def test_select_runyankole(self):
        r = req('4')
        self.assertEqual(UserLanguagePreference.get_language(PHONE), 'rn')

    def test_select_acholi(self):
        r = req('5')
        self.assertEqual(UserLanguagePreference.get_language(PHONE), 'ac')
        self.assertIn('Cik me Cua', r)   # Weather in Acholi

    def test_change_language_option_7(self):
        r = req('1*7')   # English, then change language
        self.assertIn('Choose language', r)


# ─────────────────────────────────────────────────────────────────── #
# USSD handler — main menu navigation                                  #
# ─────────────────────────────────────────────────────────────────── #

class MainMenuTest(TestCase):

    def test_english_main_menu_has_7_options(self):
        r = req('1')
        for item in ['Weather Forecast', 'Market Prices', 'Pest Diagnosis',
                     'Farming Tips', 'Ask AI', 'My Profile', 'Change Language']:
            self.assertIn(item, r)

    def test_kiswahili_main_menu(self):
        r = req('2')
        self.assertIn('Hali ya Hewa', r)
        self.assertIn('Bei za Masoko', r)
        self.assertIn('Uliza AI', r)

    def test_acholi_main_menu(self):
        r = req('5')
        self.assertIn('Cik me Cua', r)
        self.assertIn('Penyo AI', r)

    def test_exit(self):
        r = req('1*0')
        self.assertTrue(r.startswith('END'))
        self.assertIn('Goodbye', r)

    def test_exit_kiswahili(self):
        r = req('2*0')
        self.assertIn('Kwaheri', r)

    def test_invalid_main_choice(self):
        r = req('1*9')
        self.assertTrue(r.startswith('END'))


# ─────────────────────────────────────────────────────────────────── #
# Weather                                                              #
# ─────────────────────────────────────────────────────────────────── #

class WeatherMenuTest(TestCase):

    def test_weather_submenu_english(self):
        r = req('1*1')
        self.assertTrue(r.startswith('CON'))
        self.assertIn("Today's weather", r)
        self.assertIn('7-day forecast', r)

    def test_weather_submenu_kiswahili(self):
        r = req('2*1')
        self.assertIn('Hali ya Hewa', r)

    def test_back_from_weather(self):
        r = req('1*1*0')
        self.assertIn('Weather Forecast', r)   # back to main menu

    @patch('apps.weather.services.weather_api.get_current_weather')
    @patch('apps.ussd.services.ai_assistant.get_weather_farming_tip',
           return_value='Delay fertilizer — rain expected.')
    def test_today_weather_success(self, mock_tip, mock_weather):
        mock_weather.return_value = {
            'location': 'Kampala',
            'temperature': 24,
            'humidity': 70,
            'description': 'light rain',
        }
        r = req('1*1*1')
        self.assertTrue(r.startswith('END'))
        self.assertIn('Kampala', r)
        self.assertIn('24', r)

    @patch('apps.weather.services.weather_api.get_current_weather',
           side_effect=Exception("API down"))
    def test_today_weather_failure(self, _):
        r = req('1*1*1')
        self.assertTrue(r.startswith('END'))
        self.assertIn('not retrieve', r)


# ─────────────────────────────────────────────────────────────────── #
# Market prices                                                        #
# ─────────────────────────────────────────────────────────────────── #

class MarketPricesTest(TestCase):

    def test_market_submenu_english(self):
        r = req('1*2')
        self.assertIn('Maize', r)
        self.assertIn('Beans', r)
        self.assertIn('Cassava', r)
        self.assertIn('Coffee', r)

    def test_market_submenu_kiswahili(self):
        r = req('2*2')
        self.assertIn('Mahindi', r)
        self.assertIn('Maharagwe', r)

    def test_maize_price_english(self):
        r = req('1*2*1')
        self.assertTrue(r.startswith('END'))
        self.assertIn('UGX', r)

    def test_beans_price(self):
        r = req('1*2*2')
        self.assertIn('UGX', r)

    def test_invalid_market_choice(self):
        r = req('1*2*9')
        self.assertTrue(r.startswith('END'))

    def test_back_from_market(self):
        r = req('1*2*0')
        self.assertIn('Weather Forecast', r)   # back to main menu


# ─────────────────────────────────────────────────────────────────── #
# Pest diagnosis                                                       #
# ─────────────────────────────────────────────────────────────────── #

class PestDiagnosisTest(TestCase):

    def test_pest_submenu(self):
        r = req('1*3')
        self.assertIn('Pest Diagnosis', r)
        self.assertIn('Yellow', r)

    def test_pest_submenu_kiswahili(self):
        r = req('2*3')
        self.assertIn('Utambuzi wa Wadudu', r)

    @patch('apps.ussd.services.ai_assistant.get_pest_diagnosis',
           return_value='Likely Fall Armyworm. Apply neem spray. Use certified seeds next season.')
    def test_yellow_leaves_diagnosis(self, mock_diag):
        r = req('1*3*1')
        self.assertTrue(r.startswith('END'))
        self.assertIn('Fall Armyworm', r)

    def test_back_from_pest(self):
        r = req('1*3*0')
        self.assertIn('Weather Forecast', r)


# ─────────────────────────────────────────────────────────────────── #
# Farming tips                                                         #
# ─────────────────────────────────────────────────────────────────── #

class FarmingTipsTest(TestCase):

    def test_farming_tips_submenu(self):
        r = req('1*4')
        self.assertIn('Farming Tips', r)
        self.assertIn('Planting tips', r)

    def test_planting_tips_english(self):
        r = req('1*4*1')
        self.assertTrue(r.startswith('END'))
        self.assertIn('Planting', r)

    def test_pest_alerts(self):
        r = req('1*4*2')
        self.assertTrue(r.startswith('END'))
        self.assertIn('Pest', r)

    def test_harvest_advice(self):
        r = req('1*4*3')
        self.assertTrue(r.startswith('END'))
        self.assertIn('Harvest', r)

    def test_invalid_tip_choice(self):
        r = req('1*4*9')
        self.assertTrue(r.startswith('END'))


# ─────────────────────────────────────────────────────────────────── #
# Ask AI                                                               #
# ─────────────────────────────────────────────────────────────────── #

class AskAITest(TestCase):

    def test_ai_submenu_english(self):
        r = req('1*5')
        self.assertIn('Ask AI', r)
        self.assertIn('Crop advice', r)

    def test_ai_submenu_kiswahili(self):
        r = req('2*5')
        self.assertIn('Uliza AI', r)

    @patch('apps.ussd.services.ai_assistant.get_ai_response',
           return_value='Plant maize at 75x25cm spacing after first rains.')
    def test_crop_advice(self, mock_ai):
        r = req('1*5*1')
        self.assertTrue(r.startswith('END'))
        self.assertIn('maize', r)

    @patch('apps.ussd.services.ai_assistant.get_ai_response',
           return_value='Add organic compost before tilling.')
    def test_soil_tips(self, mock_ai):
        r = req('1*5*2')
        self.assertTrue(r.startswith('END'))

    @patch('apps.ussd.services.ai_assistant._call_openai', return_value=None)
    def test_ai_unavailable_fallback(self, _):
        r = req('1*5*1')
        self.assertTrue(r.startswith('END'))
        self.assertIn('unavailable', r)

    def test_back_from_ai(self):
        r = req('1*5*0')
        self.assertIn('Weather Forecast', r)


# ─────────────────────────────────────────────────────────────────── #
# USSD view (HTTP layer)                                               #
# ─────────────────────────────────────────────────────────────────── #

class USSDViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = '/ussd/callback/'

    def _post(self, text='', phone=PHONE):
        return self.client.post(self.url, {
            'sessionId': 'view-test-001',
            'serviceCode': '*384*400111#',
            'phoneNumber': phone,
            'text': text,
            'networkCode': '99999',
        })

    def test_empty_text_returns_language_menu(self):
        r = self._post('')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Choose language', r.content)
        self.assertIn(b'Acholi', r.content)

    def test_language_1_returns_main_menu(self):
        r = self._post('1')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Weather Forecast', r.content)

    def test_language_5_acholi(self):
        r = self._post('5')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Cik me Cua', r.content)

    def test_get_returns_405(self):
        r = self.client.get(self.url)
        self.assertEqual(r.status_code, 405)

    def test_market_menu_reachable(self):
        r = self._post('1*2')
        self.assertIn(b'Maize', r.content)

    def test_pest_menu_reachable(self):
        r = self._post('1*3')
        self.assertIn(b'Pest Diagnosis', r.content)
