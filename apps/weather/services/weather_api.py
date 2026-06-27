"""OpenWeatherMap API integration."""
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_current_weather(location: str) -> dict:
    """Fetch current weather for a location."""
    url = f"{settings.WEATHER_API_BASE_URL}/weather"
    params = {
        'q': location,
        'appid': settings.WEATHER_API_KEY,
        'units': 'metric',
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            'location': data.get('name'),
            'temperature': data['main']['temp'],
            'humidity': data['main']['humidity'],
            'description': data['weather'][0]['description'],
        }
    except requests.RequestException as e:
        logger.error(f"Weather API error for {location}: {e}")
        raise


def get_forecast(location: str, days: int = 7) -> list:
    """Fetch a multi-day forecast for a location."""
    url = f"{settings.WEATHER_API_BASE_URL}/forecast"
    params = {
        'q': location,
        'appid': settings.WEATHER_API_KEY,
        'units': 'metric',
        'cnt': days * 8,  # OpenWeatherMap returns data every 3h
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json().get('list', [])
    except requests.RequestException as e:
        logger.error(f"Forecast API error for {location}: {e}")
        raise
