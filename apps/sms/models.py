from django.db import models
from apps.core.models import TimeStampedModel


class SMSMessage(TimeStampedModel):
    """Records inbound and outbound SMS messages."""
    message_id = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20)
    message = models.TextField()
    direction = models.CharField(max_length=10, choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')])
    status = models.CharField(max_length=50, default='pending')

    def __str__(self):
        return f"SMS {self.direction} {self.phone_number}: {self.message[:30]}"
