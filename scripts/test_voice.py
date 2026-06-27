"""Test voice endpoints manually."""
import requests

BASE_URL = 'http://localhost:8000/api/voice'


def test_voice_callback():
    payload = {
        'sessionId': 'test-session-001',
        'callerNumber': '+254700000001',
    }
    response = requests.post(f'{BASE_URL}/callback/', data=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")


if __name__ == '__main__':
    test_voice_callback()
