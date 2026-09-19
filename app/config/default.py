import os

DEBUG = True
SECRET_KEY = 'change-this-secret-key-in-production'
BABEL_DEFAULT_LOCALE = 'en_US'
BABEL_DEFAULT_TIMEZONE = 'UTC'
TIMEZONE = 'UTC'

SQLALCHEMY_TRACK_MODIFICATIONS = False

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

MYSQL_DB = os.environ.get('MYSQL_DB', 'hieu_ho_assessment')
MYSQL_USER = os.environ.get('MYSQL_USER', 'hieu_ho')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'hieu_ho_password_123!')
MYSQL_HOST = os.environ.get('MYSQL_HOST', '127.0.0.1')
MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))

SQLALCHEMY_DATABASE_URI = (
    f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}'
    f'@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    f'?charset=utf8mb4'
)

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

MINIO_FILE = {
    'endpoint': '127.0.0.1:9000',
    'access_key': 'minioadmin',
    'secret_key': 'minioadmin',
    'secure': False,
    'bucket_name': 'assessment-files',
    'region_name': 'us-east-1',
}

UPLOAD_STATIC_URL = 'http://127.0.0.1:9000/assessment-files'

THE_DOG_API = {
    'API_DOMAIN': os.environ.get('DOG_API_DOMAIN', 'https://api.thedogapi.com/v1'),
    'API_KEY': os.environ.get('DOG_API_KEY', ''),
    'TIMEOUT': int(os.environ.get('DOG_API_TIMEOUT', 30)),
}
