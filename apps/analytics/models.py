from django.db import models
from apps.core.models import TimeStampedModel


class UsageEvent(TimeStampedModel):
    """Tracks how farmers interact with the system."""
    phone_number = models.CharField(max_length=20)
    channel = models.CharField(max_length=20, choices=[
        ('voice', 'Voice'),
        ('sms', 'SMS'),
        ('ussd', 'USSD'),
    ])
    action = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.channel} event from {self.phone_number}: {self.action}"
