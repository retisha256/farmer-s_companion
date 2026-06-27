"""Test SMS endpoints manually."""
import requests

BASE_URL = 'http://localhost:8000/api/sms'


def test_sms_callback():
    payload = {
        'from': '+254700000001',
        'to': '12345',
        'text': 'WEATHER Nairobi',
        'date': '2024-01-01 10:00:00',
    }
    response = requests.post(f'{BASE_URL}/callback/', data=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


if __name__ == '__main__':
    test_sms_callback()
