from django.db import models
from apps.core.models import TimeStampedModel


class WeatherRecord(TimeStampedModel):
    """Cached weather data for a location."""
    location = models.CharField(max_length=255)
    temperature = models.FloatField()
    humidity = models.FloatField()
    description = models.CharField(max_length=255)
    forecast_date = models.DateField()

    class Meta:
        unique_together = ('location', 'forecast_date')

    def __str__(self):
        return f"Weather at {self.location} on {self.forecast_date}"
