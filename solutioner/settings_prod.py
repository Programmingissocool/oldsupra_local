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


# --- TLS / cookie hardening (added ahead of the DNS cutover) ---
# Caddy terminates TLS and proxies to gunicorn over plain HTTP, so Django cannot
# see that the original request was HTTPS unless it trusts the forwarded header.
# Without this, request.is_secure() is always False behind the proxy and secure
# cookies would never be sent.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session/CSRF cookies must carry Secure once the site is served over HTTPS.
# Pre-cutover the site is reachable over plain HTTP on the raw IP, where Secure
# cookies would break login testing, so allow an explicit opt-out for staging.
_insecure_cookies = os.environ.get('OLDSUPRA_INSECURE_COOKIES') == '1'
SESSION_COOKIE_SECURE = not _insecure_cookies
CSRF_COOKIE_SECURE = not _insecure_cookies
SESSION_COOKIE_HTTPONLY = True


# --- SEO: robots.txt + sitemap.xml (absent upstream) ---
# django.contrib.sitemaps is not in the mirrored INSTALLED_APPS, and the routes
# must live outside i18n_patterns to be reachable at the domain root.
if 'django.contrib.sitemaps' not in INSTALLED_APPS:
    INSTALLED_APPS = list(INSTALLED_APPS) + ['django.contrib.sitemaps']

ROOT_URLCONF = 'solutioner.urls_prod'

# django.contrib.sites is required by the sitemap framework to build absolute
# URLs; SITE_ID must point at a row in django_site.
SITE_ID = globals().get('SITE_ID', 1)

# robots.txt and sitemap.xml must be reachable at the domain root. Without this
# the canonical-domain middleware rewrites them to /ka/robots.txt, which is not
# a path any crawler reads.
CANONICAL_EXEMPT_PATHS = ('/robots.txt', '/sitemap.xml')

# --- SQLite concurrency ---
# 3 gunicorn workers share one SQLite file. Default journal_mode=delete takes a
# whole-file write lock and busy_timeout=0 makes any contending request fail
# instantly with "database is locked". WAL lets readers proceed during a write,
# and the timeout makes writers queue instead of erroring.
DATABASES['default'].setdefault('OPTIONS', {})
DATABASES['default']['OPTIONS'].update({
    'init_command': 'PRAGMA journal_mode=WAL; PRAGMA busy_timeout=15000; PRAGMA synchronous=NORMAL;',
    'transaction_mode': 'IMMEDIATE',
})
