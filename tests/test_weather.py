from django.test import TestCase, Client


class WeatherAPITest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_missing_location(self):
        response = self.client.get('/api/weather/current/')
        self.assertEqual(response.status_code, 400)
