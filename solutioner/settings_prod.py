"""Deployment overrides for the my-server-3 host.

Kept separate from the mirrored settings.py so that re-syncing the source site
never clobbers deployment-specific values. Selected with
DJANGO_SETTINGS_MODULE=solutioner.settings_prod.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F401,F403

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = False

# Rotated for this host, so it no longer matches the key baked into the old
# deployment's settings.py. Read from the environment, else from .secret_key.
# Never silently fall back to the inherited literal.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    _key_file = BASE_DIR / '.secret_key'
    try:
        SECRET_KEY = _key_file.read_text().strip()
    except OSError as exc:
        raise ImproperlyConfigured(
            f'No DJANGO_SECRET_KEY set and {_key_file} is unreadable'
        ) from exc
if not SECRET_KEY:
    raise ImproperlyConfigured('SECRET_KEY is empty')

SERVER_IP = '178.105.58.108'

ALLOWED_HOSTS = [
    SERVER_IP,
    'oldsupra.ge',
    'www.oldsupra.ge',
    'localhost',
    '127.0.0.1',
]

CSRF_TRUSTED_ORIGINS = [
    'http://' + SERVER_IP,
    'https://oldsupra.ge',
    'https://www.oldsupra.ge',
]

# ForceCanonicalDomainAndLanguageMiddleware redirects everything to
# CANONICAL_HOST. Hosts listed here are served directly instead, so the site is
# reachable on the raw IP before the DNS cutover.
CANONICAL_HOST = 'oldsupra.ge'
CANONICAL_HOST_EXEMPT = (SERVER_IP, 'localhost', '127.0.0.1')

DATABASES['default']['NAME'] = BASE_DIR / 'db.sqlite3'

# Upstream settings.py declares these relative to the working directory, which
# only held on the old Passenger host. Anchor them to BASE_DIR.
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_ROOT = BASE_DIR / 'media'
STATICFILES_DIRS = [BASE_DIR / 'solutioner' / 'static']
LOCALE_PATHS = (BASE_DIR / 'locale',)
TEMPLATES[0]['DIRS'] = [BASE_DIR / 'templates']

for _handler in ('flitt_file', 'liberty_file', 'bog_file'):
    LOGGING['handlers'][_handler]['filename'] = str(
        BASE_DIR / LOGGING['handlers'][_handler]['filename']
    )
