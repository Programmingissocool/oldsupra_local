# Old Supra

Django storefront for [oldsupra.ge](https://oldsupra.ge), including the product
catalog, bilingual content, customer accounts, carts and wishlists, orders,
payment integrations, email/marketing integrations, and administration.

## Main applications

- `shop` — catalog, variants, content, banners, and promotions.
- `accounts` — customer accounts and profiles.
- `carts` — cart, wishlist, checkout, and payment callbacks.
- `orders` — orders, payments, and purchased products.
- `Project` — portfolio/project pages.
- `solutioner` — Django settings, URLs, WSGI/ASGI, and production overrides.

## Frontend source

- `templates/` contains pages, reusable includes, account and checkout views,
  and email templates.
- `solutioner/static/` contains the editable CSS, JavaScript, fonts, images, and
  bundled frontend libraries.
- The root `static/` directory is generated deployment output and is not
  tracked.
- Product and customer media is production data and is not tracked.

This is a server-rendered Django site; it has no separate React, Vue, or Angular
frontend build.

## Local setup

Python 3.12 is the verified runtime.

```bash
uv python install 3.12
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py check
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Local development uses `solutioner.settings` by default and a local SQLite
database. Do not copy the production database, media library, or credentials
into an ordinary development environment.

## Production configuration

Production uses:

- settings module `solutioner.settings_prod`;
- Gunicorn entry point `solutioner.wsgi:application`;
- SQLite with WAL and a busy timeout;
- Caddy for TLS, static/media serving, and reverse proxying; and
- environment variables for all credentials.

Copy `.env.example` to a protected `.env` and fill it from an approved secret
manager. Never commit `.env`, `.secret_key`, database files, media, logs, or
credential backups.

Typical deployment checks:

```bash
DJANGO_SETTINGS_MODULE=solutioner.settings_prod .venv/bin/python manage.py migrate
DJANGO_SETTINGS_MODULE=solutioner.settings_prod .venv/bin/python manage.py collectstatic --noinput
DJANGO_SETTINGS_MODULE=solutioner.settings_prod .venv/bin/python manage.py check --deploy
```

The production database and uploaded `media/` are persistent state and require
separate encrypted backups. They are intentionally not part of this repository.

## Security

- Keep this repository private because it contains payment and operational code.
- Supply credentials only through environment variables or an approved secret
  manager.
- Rotate any credential that was previously stored directly in source.
- Test payment changes in the provider's test environment before production.
- Do not log payment credentials, access tokens, or customer data.
