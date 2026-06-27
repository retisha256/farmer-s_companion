"""
Tests for USSD language selection, session routing, and translation service.
"""
from unittest.mock import patch

from django.test import TestCase, Client

from apps.ussd.models import UserLanguagePreference
from apps.ussd.services.ussd_handler import handle_ussd_request
from apps.ussd.services.translations import translate, get_menu, SUPPORTED_LANGUAGES


# ------------------------------------------------------------------ #
# Translation service tests                                            #
# ------------------------------------------------------------------ #

class TranslationServiceTest(TestCase):

    def test_english_returns_original(self):
        self.assertEqual(translate("0. Exit", 'en'), "0. Exit")

    def test_kiswahili_exit(self):
        result = translate("0. Exit", 'sw')
        self.assertEqual(result, '0. Toka')

    def test_luganda_exit(self):
        result = translate("0. Exit", 'lg')
        self.assertEqual(result, '0. Vamu')

    def test_runyankole_exit(self):
        result = translate("0. Exit", 'rn')
        self.assertEqual(result, '0. Sohoka')

    def test_unknown_language_returns_english(self):
        result = translate("0. Exit", 'xx')
        self.assertEqual(result, "0. Exit")

    def test_missing_key_returns_original(self):
        result = translate("Some untranslated string", 'sw')
        self.assertEqual(result, "Some untranslated string")

    def test_get_menu_english(self):
        menu = get_menu(["Market Prices", "1. Maize"], 'en')
        self.assertTrue(menu.startswith("CON "))
        self.assertIn("Market Prices", menu)
        self.assertIn("1. Maize", menu)

    def test_get_menu_kiswahili(self):
        menu = get_menu(["Market Prices", "1. Maize"], 'sw')
        self.assertIn("Bei za Masoko", menu)
        self.assertIn("1. Mahindi", menu)

    def test_get_menu_end_prefix(self):
        menu = get_menu(["Some message"], 'en', prefix='END')
        self.assertTrue(menu.startswith("END "))

    def test_all_supported_languages_defined(self):
        self.assertIn('en', SUPPORTED_LANGUAGES)
        self.assertIn('sw', SUPPORTED_LANGUAGES)
        self.assertIn('lg', SUPPORTED_LANGUAGES)
        self.assertIn('rn', SUPPORTED_LANGUAGES)


# ------------------------------------------------------------------ #
# UserLanguagePreference model tests                                   #
# ------------------------------------------------------------------ #

class UserLanguagePreferenceTest(TestCase):

    def test_default_language_is_english(self):
        lang = UserLanguagePreference.get_language('+256700000001')
        self.assertEqual(lang, 'en')

    def test_set_and_get_language(self):
        UserLanguagePreference.set_language('+256700000001', 'sw')
        lang = UserLanguagePreference.get_language('+256700000001')
        self.assertEqual(lang, 'sw')

    def test_update_existing_preference(self):
        UserLanguagePreference.set_language('+256700000002', 'sw')
        UserLanguagePreference.set_language('+256700000002', 'lg')
        lang = UserLanguagePreference.get_language('+256700000002')
        self.assertEqual(lang, 'lg')

    def test_str_representation(self):
        pref = UserLanguagePreference.objects.create(
            phone_number='+256700000003',
            preferred_language='rn',
        )
        self.assertIn('+256700000003', str(pref))
        self.assertIn('Runyankole', str(pref))


# ------------------------------------------------------------------ #
# USSD handler tests                                                   #
# ------------------------------------------------------------------ #

class USSDHandlerTest(TestCase):

    PHONE = '+256701066872'
    SESSION = 'test-session-001'

    def _req(self, text):
        return handle_ussd_request(self.SESSION, self.PHONE, text)

    # ── Language selection ──────────────────────────────────────────

    def test_empty_text_shows_language_menu_new_user(self):
        response = self._req('')
        self.assertTrue(response.startswith('CON'))
        self.assertIn('Choose language', response)
        self.assertIn('English', response)
        self.assertIn('Kiswahili', response)
        self.assertIn('Luganda', response)
        self.assertIn('Runyankole', response)

    def test_returning_user_skips_language_menu(self):
        UserLanguagePreference.set_language(self.PHONE, 'sw')
        response = self._req('')
        # Should go straight to main menu in Kiswahili
        self.assertTrue(response.startswith('CON'))
        self.assertIn('Karibu', response)  # Kiswahili welcome

    def test_select_english(self):
        response = self._req('1')
        self.assertTrue(response.startswith('CON'))
        lang = UserLanguagePreference.get_language(self.PHONE)
        self.assertEqual(lang, 'en')

    def test_select_kiswahili(self):
        response = self._req('2')
        lang = UserLanguagePreference.get_language(self.PHONE)
        self.assertEqual(lang, 'sw')
        self.assertIn('Hali ya Hewa', response)  # Kiswahili weather

    def test_select_luganda(self):
        response = self._req('3')
        lang = UserLanguagePreference.get_language(self.PHONE)
        self.assertEqual(lang, 'lg')

    def test_select_runyankole(self):
        response = self._req('4')
        lang = UserLanguagePreference.get_language(self.PHONE)
        self.assertEqual(lang, 'rn')

    # ── Main menu navigation ─────────────────────────────────────────

    def test_english_main_menu(self):
        response = self._req('1')  # select English
        self.assertIn('Weather Forecast', response)
        self.assertIn('Market Prices', response)
        self.assertIn('Crop Advisory', response)
        self.assertIn('My Profile', response)

    def test_kiswahili_main_menu(self):
        response = self._req('2')  # select Kiswahili
        self.assertIn('Hali ya Hewa', response)
        self.assertIn('Bei za Masoko', response)

    # ── Weather sub-menu ─────────────────────────────────────────────

    def test_weather_submenu_english(self):
        response = self._req('1*1')
        self.assertTrue(response.startswith('CON'))
        self.assertIn('Weather Forecast', response)

    def test_weather_submenu_kiswahili(self):
        response = self._req('2*1')
        self.assertIn('Hali ya Hewa', response)

    # ── Market prices ────────────────────────────────────────────────

    def test_market_submenu_english(self):
        response = self._req('1*2')
        self.assertTrue(response.startswith('CON'))
        self.assertIn('Maize', response)

    def test_market_submenu_kiswahili(self):
        response = self._req('2*2')
        self.assertIn('Mahindi', response)

    # ── Crop advisory ────────────────────────────────────────────────

    def test_crop_advisory_submenu(self):
        response = self._req('1*3')
        self.assertTrue(response.startswith('CON'))
        self.assertIn('Planting', response)

    # ── Change language (option 5) ───────────────────────────────────

    def test_change_language_option(self):
        response = self._req('1*5')
        self.assertTrue(response.startswith('CON'))
        self.assertIn('Choose language', response)

    # ── Exit ─────────────────────────────────────────────────────────

    def test_exit_english(self):
        response = self._req('1*0')
        self.assertTrue(response.startswith('END'))
        self.assertIn('Goodbye', response)

    def test_exit_kiswahili(self):
        response = self._req('2*0')
        self.assertTrue(response.startswith('END'))
        self.assertIn('Kwaheri', response)

    # ── Invalid input ────────────────────────────────────────────────

    def test_invalid_main_menu_choice(self):
        response = self._req('1*9')
        self.assertTrue(response.startswith('END'))
        self.assertIn('Invalid', response)

    def test_invalid_market_choice(self):
        response = self._req('1*2*9')
        self.assertTrue(response.startswith('END'))


# ------------------------------------------------------------------ #
# USSD view (HTTP) tests                                               #
# ------------------------------------------------------------------ #

class USSDViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = '/ussd/callback/'

    def _post(self, text='', phone='+256701066872', session='view-test-001'):
        return self.client.post(self.url, {
            'sessionId': session,
            'serviceCode': '*384*400111#',
            'phoneNumber': phone,
            'text': text,
            'networkCode': '99999',
        })

    def test_empty_text_returns_language_menu(self):
        resp = self._post('')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Choose language', resp.content)

    def test_language_selection_returns_main_menu(self):
        resp = self._post('1')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Weather Forecast', resp.content)

    def test_get_request_returns_405(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 405)

    def test_kiswahili_selection(self):
        resp = self._post('2')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Hali ya Hewa', resp.content)
