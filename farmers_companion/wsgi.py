"""WSGI config for farmers_companion project."""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'farmers_companion.settings')

application = get_wsgi_application()
