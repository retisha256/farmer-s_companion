"""Market price service — fetches current crop market prices."""
import requests
import logging

logger = logging.getLogger('apps.sms')


def get_market_prices(crop: str, region: str) -> dict:
    """
    Fetch market prices for a given crop in a region.
    Returns a dict with price info or raises on failure.
    """
    # TODO: integrate with a real market data provider or scraper
    logger.info(f"Fetching market price for {crop} in {region}")
    mock_data = {
        'crop': crop,
        'region': region,
        'price_per_kg': 0.0,
        'currency': 'KES',
        'source': 'mock',
    }
    return mock_data
