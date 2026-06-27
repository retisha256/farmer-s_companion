"""farmers_companion URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Import callback views directly for the AT shortcut URLs
# This avoids duplicate namespace warnings from re-including the same app url modules
from apps.ussd.views import ussd_callback
from apps.sms.views import sms_callback
from apps.voice.views import voice_callback

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),

    # Africa's Talking webhook URLs — paste these into your AT dashboard
    # e.g. https://<ngrok>.ngrok.io/ussd/callback/
    path('ussd/callback/', ussd_callback, name='at_ussd_callback'),
    path('sms/callback/',  sms_callback,  name='at_sms_callback'),
    path('voice/callback/', voice_callback, name='at_voice_callback'),

    # Full API routes
    path('api/voice/', include('apps.voice.urls')),
    path('api/sms/', include('apps.sms.urls')),
    path('api/ussd/', include('apps.ussd.urls')),
    path('api/weather/', include('apps.weather.urls')),
    path('api/farmers/', include('apps.farmers.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
