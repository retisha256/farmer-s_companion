from django.test import TestCase, Client


class SMSCallbackTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_sms_callback_post(self):
        response = self.client.post('/api/sms/callback/', {
            'from': '+254700000001',
            'text': 'WEATHER Nairobi',
        })
        self.assertEqual(response.status_code, 200)
