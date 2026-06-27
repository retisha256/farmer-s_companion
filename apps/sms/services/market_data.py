"""
Market price service.

Data source priority:
  1. Django cache (1 hour TTL) — avoids hammering the API
  2. Real API call (configurable endpoint)
  3. Fallback to Uganda baseline prices if API is unavailable

The service returns prices in UGX (Ugandan Shillings).
Supported crops: maize, beans, cassava, coffee, wheat, tomatoes, rice
"""
import logging
from datetime import datetime

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger('apps.sms')

_CACHE_TTL = 3_600   # 1 hour

# Uganda baseline prices (UGX/kg) — sourced from UCDA/MAAIF averages
# Updated periodically; used as fallback when live API is unavailable.
_BASELINE_PRICES_UGX: dict[str, dict] = {
    'Maize':    {'price_per_kg': 1_200, 'market': 'Kampala'},
    'Beans':    {'price_per_kg': 4_200, 'market': 'Kampala'},
    'Cassava':  {'price_per_kg': 600,   'market': 'Kampala'},
    'Coffee':   {'price_per_kg': 12_000, 'market': 'Kampala'},
    'Wheat':    {'price_per_kg': 1_800, 'market': 'Kampala'},
    'Tomatoes': {'price_per_kg': 1_500, 'market': 'Kampala'},
    'Rice':     {'price_per_kg': 3_500, 'market': 'Kampala'},
}


def get_market_prices(crop: str, region: str = 'Uganda') -> dict:
    """
    Fetch market prices for a crop.

    Returns:
        {
          'crop': str,
          'region': str,
          'price_per_kg': float,
          'currency': 'UGX',
          'market': str,
          'source': 'live' | 'baseline',
          'as_of': str  (ISO date)
        }
    """
    crop_key = crop.title()
    cache_key = f"market_{crop_key.lower()}_{region.lower()}"

    cached = cache.get(cache_key)
    if cached:
        logger.debug("Market price cache hit for %s/%s", crop_key, region)
        return cached

    # Try live API
    result = _fetch_live_price(crop_key, region)

    # Fall back to baseline
    if not result:
        result = _baseline_price(crop_key, region)

    cache.set(cache_key, result, _CACHE_TTL)
    return result


def get_multiple_prices(crops: list[str], region: str = 'Uganda') -> list[dict]:
    """Fetch prices for a list of crops."""
    return [get_market_prices(crop, region) for crop in crops]


# ------------------------------------------------------------------ #
# Internal helpers                                                     #
# ------------------------------------------------------------------ #

def _fetch_live_price(crop: str, region: str) -> dict | None:
    """
    Attempt to fetch a live price from the configured MARKET_API_URL.
    Returns None if the key is not configured or the request fails.

    To enable, add to .env:
      MARKET_API_URL=https://your-price-api.com/prices
      MARKET_API_KEY=your-key
    """
    api_url = getattr(settings, 'MARKET_API_URL', '')
    api_key = getattr(settings, 'MARKET_API_KEY', '')

    if not api_url:
        return None

    try:
        response = requests.get(
            api_url,
            params={'crop': crop, 'region': region, 'currency': 'UGX'},
            headers={'Authorization': f'Bearer {api_key}'} if api_key else {},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        return {
            'crop': crop,
            'region': region,
            'price_per_kg': float(data.get('price_per_kg', 0)),
            'currency': data.get('currency', 'UGX'),
            'market': data.get('market', region),
            'source': 'live',
            'as_of': data.get('date', datetime.now().date().isoformat()),
        }
    except Exception as exc:
        logger.warning("Live market API failed for %s: %s", crop, exc)
        return None


def _baseline_price(crop: str, region: str) -> dict:
    """Return Uganda baseline prices as a fallback."""
    baseline = _BASELINE_PRICES_UGX.get(crop, {
        'price_per_kg': 0,
        'market': region,
    })
    return {
        'crop': crop,
        'region': region,
        'price_per_kg': baseline['price_per_kg'],
        'currency': 'UGX',
        'market': baseline.get('market', 'Kampala'),
        'source': 'baseline',
        'as_of': datetime.now().date().isoformat(),
    }
