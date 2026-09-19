# hieu-ho-python-assessment

## Architecture

```
app/
  __init__.py        # create_app(): config -> babel -> db -> APIs -> jinja
  api/
    __init__.py      # auto-discovers namespaces under frontend/ and admin/
    common/          # Api/Namespace/Resource base classes, decorators, responses
    frontend/        # public APIs   -> /frontend/*
    admin/           # admin APIs    -> /admin/*
  business/          # business logic layer (no Flask/HTTP concerns)
  caches/            # cache layer (in-memory stub; swap for Redis when needed)
  common/            # shared constants
  config/            # default.py + optional testing.py / environment.py overlays
  exceptions/        # typed exceptions mapped to error codes
  models/            # SQLAlchemy models, db session helpers
  utils/             # helpers (dates, random, text, ...)
manage.py            # Flask CLI entry point (+ `init-data`)
run.py               # dev server entry point
```

Each module under `app/api/frontend/` and `app/api/admin/` that exposes a module-level
`ns = Namespace(...)` is mounted automatically at `/<blueprint>/<module-name>`, so adding
an endpoint group means adding one file — no registration boilerplate.

Responses go through `@respond_with_code`, producing a uniform envelope:

```json
{"code": 0, "data": {...}, "message": "Success"}
```

Errors raised as `app.exceptions.*` subclasses are turned into the same envelope with a
non-zero `code`.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create testing config
```bash
cp app/config/testing_example.py app/config/testing.py
```

Config create order: `default.py` -> `testing.py` -> `environment.py`

## Running

```bash
# create the schema and seed demo users
python manage.py <INIT_FUNCTION>

# dev server on http://127.0.0.1:5000
python run.py
```

```bash
curl -s -X POST localhost:5000/frontend/user/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user1@example.com","password":"User123!"}'

curl -s localhost:5000/frontend/user/me -H "AUTHORIZATION: <token>"
```