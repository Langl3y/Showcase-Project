# hieu-ho-python-assessment

A minimal Flask backend stub derived from the PayAny backend architecture. It keeps the
layering, conventions and plumbing of the original project, but ships only a small
user/system slice so a new project can be grown on top of it.

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

Optional local overrides: copy `app/config/testing_example.py` to `app/config/testing.py`
(git-ignored) and adjust. Config files are layered in this order:
`default.py` -> `testing.py` -> `environment.py`, later files overriding earlier ones.

## Running

```bash
# create the schema and seed demo users
python manage.py init-data

# dev server on http://127.0.0.1:5000
python run.py
```

Swagger UI: http://127.0.0.1:5000/frontend/swagger/ and /admin/swagger/
(controlled by `EXPOSED_DOCS` in the config).

On macOS port 5000 is often taken by the AirPlay Receiver (it answers with `403`); run
`flask --app run:app run --port 5001` instead, or turn AirPlay Receiver off.

Seeded users: `admin@example.com` / `Admin123!`, `user1@example.com` / `User123!`,
`user2@example.com` / `User123!`.

## Endpoints

| Method     | Path                          | Notes                          |
|------------|-------------------------------|--------------------------------|
| GET        | /frontend/system/health       | liveness probe                 |
| GET        | /frontend/system/info         | service metadata               |
| POST       | /frontend/user/register       | email + password (+ username)  |
| POST       | /frontend/user/login          | returns a bearer-style token   |
| POST       | /frontend/user/logout         | requires `AUTHORIZATION`       |
| GET        | /frontend/user/me             | requires `AUTHORIZATION`       |
| GET        | /admin/user/users             | paginated list                 |
| GET, PUT   | /admin/user/users/<user_id>   | fetch / update a user          |

Authenticated calls pass the login token in the `AUTHORIZATION` header.

```bash
curl -s -X POST localhost:5000/frontend/user/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user1@example.com","password":"User123!"}'

curl -s localhost:5000/frontend/user/me -H "AUTHORIZATION: <token>"
```

## Tests

```bash
pytest
```

Tests run against an isolated temporary SQLite database; nothing in `app/` is touched.

## Notes on what was left out

Relative to the source project, this stub drops the domain modules (balances, assets,
cards, crypto, ptp, gift cards, rates, ...), Celery tasks and schedules, the wallet/RPC
integrations and the Alembic migration history. The cache layer is an in-memory dict
rather than Redis, and the database defaults to SQLite. The intent is that new domains
are added as new `models/` + `business/` + `api/` triplets following the same pattern as
the `user` slice.
