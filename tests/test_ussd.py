from django.test import TestCase, Client


class USSDCallbackTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_main_menu(self):
        response = self.client.post('/api/ussd/callback/', {
            'sessionId': 'test-ussd-001',
            'phoneNumber': '+254700000001',
            'text': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'CON', response.content)

    def test_exit(self):
        response = self.client.post('/api/ussd/callback/', {
            'sessionId': 'test-ussd-002',
            'phoneNumber': '+254700000001',
            'text': '0',
        })
        self.assertIn(b'END', response.content)
