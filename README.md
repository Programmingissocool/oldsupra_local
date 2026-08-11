# OldSupra.ge

Source code for the OldSupra.ge online shop, imported from the `my-server-3` deployment.

## Stack

- Python and Django 5.1
- SQLite for the current database configuration
- Django templates with HTML, CSS, and JavaScript
- Bootstrap and jQuery-based frontend assets
- Gunicorn in production, with WhiteNoise for static files
- Mailjet through Django Anymail for outbound email
- Omnisend API for marketing and cart/order events
- Bank of Georgia, TBC, Flitt, and Liberty/Pay.ge payment integrations

## Frontend source

- `templates/` contains page layouts, reusable includes, account pages, shop pages, checkout, and email templates.
- `solutioner/static/` contains the editable CSS, JavaScript, fonts, images, and bundled frontend libraries.
- The root `static/` directory is generated deployment output and is intentionally not tracked.
- Product/customer media is production data and is intentionally not tracked.

This is a server-rendered Django site; there is no separate React, Vue, or Angular frontend build.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
set -a
source .env
set +a
python manage.py migrate
python manage.py runserver
```

The repository does not contain the production database, uploaded media, logs, production environment files, or API credentials. A new local database is created by `migrate`.

The default `solutioner.settings` module is suitable for local development. Production uses `solutioner.settings_prod` and requires a real `DJANGO_SECRET_KEY` (or an untracked `.secret_key` file) plus the relevant integration credentials.
