# Agent Instructions

## Local Django Admin

The admin starts with the same Django server as the storefront; it is available at `/admin/`.

```bash
git clone git@github.com:nikibreg/oldsupra.git
cd oldsupra

uv python install 3.12
uv venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt

.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

Then open `http://127.0.0.1:8000/admin/`.