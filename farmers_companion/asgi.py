"""ASGI config for farmers_companion project."""

import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmers_companion.settings')

application = get_asgi_application()
