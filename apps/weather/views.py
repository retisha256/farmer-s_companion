from django.http import JsonResponse
from .services.weather_api import get_current_weather


def weather_by_location(request):
    """Return current weather for a given location query parameter."""
    location = request.GET.get('location', '')
    if not location:
        return JsonResponse({'error': 'location parameter is required'}, status=400)
    try:
        data = get_current_weather(location)
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
