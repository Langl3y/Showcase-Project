DEBUG = True
SECRET_KEY = 'testing-secret-key'

SQLALCHEMY_TRACK_MODIFICATIONS = False

import os
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'test_app.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'

DB_ENGINE_OPTIONS = {
    'DB_POOL_SIZE': 5,
    'DB_POOL_MAX_OVERFLOW': 10,
    'DB_POOL_RECYCLE': 3600,
    'DB_POOL_PING': True,
    'DB_POOL_TIMEOUT': 30,
}

THE_DOG_API_KEY=''
