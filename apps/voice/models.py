from django.db import models
from apps.core.models import TimeStampedModel


class VoiceCall(TimeStampedModel):
    """Records incoming/outgoing voice calls."""
    session_id = models.CharField(max_length=255, unique=True)
    caller_number = models.CharField(max_length=20)
    direction = models.CharField(max_length=10, choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')])
    duration = models.IntegerField(default=0)
    recording_url = models.URLField(blank=True, null=True)
    transcript = models.TextField(blank=True)

    def __str__(self):
        return f"{self.direction} call from {self.caller_number}"
