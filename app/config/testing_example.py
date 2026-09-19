DEBUG = True
SECRET_KEY = 'testing-secret-key'

SQLALCHEMY_TRACK_MODIFICATIONS = False

import os

MYSQL_DB = os.environ.get('MYSQL_DB', 'hieu_ho_assessment_test')
MYSQL_USER = os.environ.get('MYSQL_USER', 'hieu_ho')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

SQLALCHEMY_DATABASE_URI = (
    f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}'
    f'@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    f'?charset=utf8mb4'
)

DB_ENGINE_OPTIONS = {
    'DB_POOL_SIZE': 5,
    'DB_POOL_MAX_OVERFLOW': 10,
    'DB_POOL_RECYCLE': 3600,
    'DB_POOL_PING': True,
    'DB_POOL_TIMEOUT': 30,
}

THE_DOG_API = {
    'API_DOMAIN': 'https://api.thedogapi.com/v1',
    'API_KEY': '',
    'TIMEOUT': 30,
}
