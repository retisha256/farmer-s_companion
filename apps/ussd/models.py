from django.db import models
from apps.core.models import TimeStampedModel


class USSDSession(TimeStampedModel):
    """Tracks a USSD session and its accumulated input."""
    session_id = models.CharField(max_length=255, unique=True)
    phone_number = models.CharField(max_length=20)
    text_history = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"USSD session {self.session_id} - {self.phone_number}"


class UserLanguagePreference(TimeStampedModel):
    """
    Stores the language a farmer chose via USSD.
    One record per phone number — updated on each new selection.
    """
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('sw', 'Kiswahili'),
        ('lg', 'Luganda'),
        ('rn', 'Runyankole'),
        ('ac', 'Acholi'),
    ]

    phone_number = models.CharField(max_length=20, unique=True)
    preferred_language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en',
    )

    class Meta:
        verbose_name = 'User Language Preference'
        verbose_name_plural = 'User Language Preferences'

    def __str__(self):
        return f"{self.phone_number} → {self.get_preferred_language_display()}"

    @classmethod
    def get_language(cls, phone_number: str) -> str:
        """Return the stored language code for a number, defaulting to 'en'."""
        try:
            return cls.objects.get(phone_number=phone_number).preferred_language
        except cls.DoesNotExist:
            return 'en'

    @classmethod
    def set_language(cls, phone_number: str, language_code: str) -> None:
        """Persist or update the language preference for a number."""
        cls.objects.update_or_create(
            phone_number=phone_number,
            defaults={'preferred_language': language_code},
        )
        # Also sync to Farmer profile if it exists
        try:
            from apps.farmers.models import Farmer
            Farmer.objects.filter(phone_number=phone_number).update(language=language_code)
        except Exception:
            pass
