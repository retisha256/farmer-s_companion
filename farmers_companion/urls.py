"""farmers_companion URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),

    # Africa's Talking webhook shortcuts (configure these URLs in your AT dashboard)
    path('ussd/callback/', include('apps.ussd.urls')),   # → apps.ussd.urls  (shortcut)
    path('sms/callback/',  include('apps.sms.urls')),    # → apps.sms.urls   (shortcut)
    path('voice/callback/', include('apps.voice.urls')), # → apps.voice.urls (shortcut)

    # API routes
    path('api/voice/', include('apps.voice.urls')),
    path('api/sms/', include('apps.sms.urls')),
    path('api/ussd/', include('apps.ussd.urls')),
    path('api/weather/', include('apps.weather.urls')),
    path('api/farmers/', include('apps.farmers.urls')),
    path('api/payments/', include('apps.payments.urls')),
    path('api/analytics/', include('apps.analytics.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
