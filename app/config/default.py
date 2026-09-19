import os

DEBUG = True
SECRET_KEY = 'change-this-secret-key-in-production'
BABEL_DEFAULT_LOCALE = 'en_US'
BABEL_DEFAULT_TIMEZONE = 'UTC'
TIMEZONE = 'UTC'

SQLALCHEMY_TRACK_MODIFICATIONS = False

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'app.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'

DB_ENGINE_OPTIONS = {
    'DB_POOL_SIZE': 10,
    'DB_POOL_MAX_OVERFLOW': 20,
    'DB_POOL_RECYCLE': 3600,
    'DB_POOL_PING': True,
    'DB_POOL_TIMEOUT': 30,
}

REDIS = {
    'host': '127.0.0.1',
    'port': 6379,
    'db': 0,
}

EXPOSED_DOCS = ['frontend', 'admin']
DEFAULT_TEST_TOKEN = ''

WEB_MAX_PAGE = 100
WEB_MAX_LIMIT = 200
