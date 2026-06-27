from django.db import models
from apps.core.models import TimeStampedModel


class USSDSession(TimeStampedModel):
    """Tracks a USSD session."""
    session_id = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20)
    text_history = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"USSD session {self.session_id} - {self.phone_number}"
