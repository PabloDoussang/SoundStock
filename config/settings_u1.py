"""Entrega U1: datos simulados en JSON y sesiones firmadas, sin base de datos."""
from .settings import *
from copy import deepcopy

DATABASES = {}
ROOT_URLCONF = 'config.urls_u1'
SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'
SESSION_COOKIE_NAME = 'musicpro_u1_session'
CSRF_COOKIE_NAME = 'musicpro_u1_csrf'
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django.contrib.admin'] + ['u1']
MIDDLEWARE = [
    'u1.middleware.MockUserMiddleware' if item == 'django.contrib.auth.middleware.AuthenticationMiddleware' else item
    for item in MIDDLEWARE
]
TEMPLATES = deepcopy(TEMPLATES)
TEMPLATES[0]['OPTIONS']['context_processors'] = [
    'u1.middleware.user_context' if item == 'django.contrib.auth.context_processors.auth' else item
    for item in TEMPLATES[0]['OPTIONS']['context_processors']
]
U1_DATA_FILE = BASE_DIR / 'runtime' / 'u1.json'
