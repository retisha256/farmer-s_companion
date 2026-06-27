from django.db import models
from apps.core.models import TimeStampedModel


class Location(TimeStampedModel):
    """Geographic location."""
    name = models.CharField(max_length=255)
    county = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Kenya')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return self.name


class Crop(TimeStampedModel):
    """A crop type."""
    name = models.CharField(max_length=100, unique=True)
    season = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Farmer(TimeStampedModel):
    """Farmer profile."""
    phone_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255, blank=True)
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, blank=True)
    crops = models.ManyToManyField(Crop, blank=True)
    language = models.CharField(max_length=10, default='en')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.phone_number})"
