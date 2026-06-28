from django.db import models
from apps.core.models import TimeStampedModel


class VoiceCall(TimeStampedModel):
    """Audit log of every call that hits the system."""
    session_id = models.CharField(max_length=255, unique=True)
    caller_number = models.CharField(max_length=20)
    direction = models.CharField(
        max_length=10,
        choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')],
    )
    duration = models.IntegerField(default=0)
    recording_url = models.URLField(blank=True, null=True)
    transcript = models.TextField(blank=True)

    def __str__(self):
        return f"{self.direction} call from {self.caller_number}"


class VoiceSession(TimeStampedModel):
    """
    Tracks live voice session state across multiple AT hops.

    Unlike USSD (which accumulates all input in one `text` field),
    each voice hop is a separate HTTP request.  We persist state here
    so each hop knows where in the menu tree the caller is.
    """
    # State constants — match the values in voice_session.py
    INIT            = 'INIT'
    LANGUAGE_SELECT = 'LANGUAGE_SELECT'
    MAIN_MENU       = 'MAIN_MENU'
    WEATHER_MENU    = 'WEATHER_MENU'
    MARKET_MENU     = 'MARKET_MENU'
    PEST_MENU       = 'PEST_MENU'
    FARMING_TIPS    = 'FARMING_TIPS'
    AI_MENU         = 'AI_MENU'
    HANGUP          = 'HANGUP'

    STATE_CHOICES = [
        (INIT,            'Init'),
        (LANGUAGE_SELECT, 'Language Selection'),
        (MAIN_MENU,       'Main Menu'),
        (WEATHER_MENU,    'Weather Menu'),
        (MARKET_MENU,     'Market Menu'),
        (PEST_MENU,       'Pest Menu'),
        (FARMING_TIPS,    'Farming Tips'),
        (AI_MENU,         'AI Menu'),
        (HANGUP,          'Hangup'),
    ]

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('sw', 'Kiswahili'),
        ('lg', 'Luganda'),
        ('rn', 'Runyankole'),
        ('ac', 'Acholi'),
    ]

    session_id    = models.CharField(max_length=255, unique=True)
    caller_number = models.CharField(max_length=20)
    direction     = models.CharField(
        max_length=10,
        choices=[('inbound', 'Inbound'), ('outbound', 'Outbound')],
        default='inbound',
    )
    state         = models.CharField(max_length=20, choices=STATE_CHOICES, default=INIT)
    language      = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, default='en')
    is_active     = models.BooleanField(default=True)
    digits_log    = models.TextField(blank=True, help_text="All DTMF digits received, comma-separated")

    class Meta:
        verbose_name = 'Voice Session'
        verbose_name_plural = 'Voice Sessions'

    def __str__(self):
        return f"Voice session {self.session_id} ({self.caller_number}) [{self.state}]"
