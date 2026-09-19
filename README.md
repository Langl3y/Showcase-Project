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
  utils/             # helpers (dates, random, text, files/minio, ...)
manage.py            # Flask CLI entry point (+ `init-data` command)
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

Config create order: `default.py` -> `testing.py` -> `environment.py`. MySQL
credentials can be overridden via env vars `MYSQL_DB`, `MYSQL_USER`,
`MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_PORT`.

## MySQL Setup

### macOS / Homebrew

```bash
# 1. Install + start MySQL
brew install mysql
brew services start mysql
# default root password set on fresh install: `root` (if changed, use yours)
```

### Ubuntu / Debian Linux

```bash
# 1. Install + start MySQL (server + client)
sudo apt-get update
sudo apt-get install -y mysql-server mysql-client
sudo systemctl enable --now mysql

# 1b. Secure a fresh install: set root password, remove anonymous users,
#     disable remote root login, drop test database. Choose `Y` when prompted
#     for "Disallow root login remotely?" to keep things local.
sudo mysql_secure_installation
```

Ubuntu 22.04+ ships MySQL 8 with `auth_socket` for `root@localhost` by default,
so login as root with `sudo mysql` (no password) instead of `mysql -uroot -p`.
If you'd rather use password-based root login, run:

```bash
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'root'; FLUSH PRIVILEGES;"
```

### Create database + user (same on macOS and Linux)

Use `mysql -uroot -proot` (Homebrew default) or `sudo mysql` (Ubuntu socket auth)
depending on how you installed.

```bash
# 2. Create the database + user (run once)
mysql -uroot -proot <<'SQL'
CREATE DATABASE IF NOT EXISTS hieu_ho_assessment
  DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'hieu_ho'@'localhost'
  IDENTIFIED BY 'hieu_ho_password_123!';
GRANT ALL PRIVILEGES ON hieu_ho_assessment.* TO 'hieu_ho'@'localhost'
  WITH GRANT OPTION;
CREATE USER IF NOT EXISTS 'hieu_ho'@'127.0.0.1'
  IDENTIFIED BY 'hieu_ho_password_123!';
GRANT ALL PRIVILEGES ON hieu_ho_assessment.* TO 'hieu_ho'@'127.0.0.1'
  WITH GRANT OPTION;
FLUSH PRIVILEGES;
SQL

# 2b. Create test database if you run pytest (optional)
mysql -uroot -proot <<'SQL'
CREATE DATABASE IF NOT EXISTS hieu_ho_assessment_test
  DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_unicode_ci;
GRANT ALL PRIVILEGES ON hieu_ho_assessment_test.* TO 'hieu_ho'@'localhost'
  WITH GRANT OPTION;
GRANT ALL PRIVILEGES ON hieu_ho_assessment_test.* TO 'hieu_ho'@'127.0.0.1'
  WITH GRANT OPTION;
FLUSH PRIVILEGES;
SQL

# 3. Verify connection
mysql -u hieu_ho -p'hieu_ho_password_123!' -h 127.0.0.1 hieu_ho_assessment \
  -e "SELECT DATABASE();"
```

## Running

```bash
# create MySQL tables, seed demo users, import all breeds from THE_DOG_API /breeds
python3 manage.py init-data

# verify 3 tables got populated
mysql -u hieu_ho -p'hieu_ho_password_123!' -h 127.0.0.1 hieu_ho_assessment \
  -e "SELECT 'user' AS tbl, COUNT(*) AS n FROM user UNION ALL
      SELECT 'breed', COUNT(*) FROM breed UNION ALL
      SELECT 'species', COUNT(*) FROM species UNION ALL
      SELECT 'breed_image', COUNT(*) FROM breed_image UNION ALL
      SELECT 'file', COUNT(*) FROM file;"

# dev server on http://127.0.0.1:5000
python3 run.py
```

```bash
curl -s -X POST localhost:5000/frontend/user/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"user1@example.com","password":"User123!"}'

curl -s localhost:5000/frontend/user/me -H "AUTHORIZATION: <token>"
```

### Database migrations

```bash
# Apply outstanding migrations
python3 manage.py db upgrade

# Migrate new updates from model -> DB
python3 manage.py db migrate -m "what changed"
python3 manage.py db upgrade

# Get metadata
python3 manage.py db current     # Get current revision
python3 manage.py db history     # Get all revisions
python3 manage.py db downgrade   # Downgrade from current revision
```

A database created before migrations existed already has the tables, so mark it
as up to date once instead of upgrading: `python3 manage.py db stamp head`.

### Init data

Run the Flask shell
```bash
python3 manage.py shell
```

```python
from app.business import init_data, init_users, init_breeds

init_users()   # init default users
init_breeds()  # fetch fresh breed data from the dog api
init_data()    # run all init functions above
```
