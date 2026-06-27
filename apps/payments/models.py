from django.db import models
from apps.core.models import TimeStampedModel
from apps.farmers.models import Farmer


class Payment(TimeStampedModel):
    """Records a payment or airtime transaction."""
    farmer = models.ForeignKey(Farmer, on_delete=models.CASCADE, related_name='payments')
    transaction_id = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='KES')
    status = models.CharField(max_length=50, default='pending')
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} {self.currency}"
