from django.test import TestCase, Client


class VoiceCallbackTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_voice_callback_post(self):
        response = self.client.post('/api/voice/callback/', {
            'sessionId': 'test-001',
            'callerNumber': '+254700000001',
        })
        self.assertEqual(response.status_code, 200)

    def test_voice_callback_get_not_allowed(self):
        response = self.client.get('/api/voice/callback/')
        self.assertEqual(response.status_code, 405)
