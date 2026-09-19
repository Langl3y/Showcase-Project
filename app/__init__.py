from logging import Logger, getLogger
from typing import Optional

from flask import Flask
from flask_babel import Babel
from flask_migrate import Migrate

from .config import config

app: Optional[Flask] = None
_logger: Optional[Logger] = None
migrate: Optional[Migrate] = None
babel: Optional[Babel] = None


def create_app():
    global app
    app = Flask(__name__)
    _init_logging()
    _init_config(app)
    _init_babel(app)
    _init_db(app)
    _init_apis(app)
    _init_jinja(app)
    _logger.info('server started successfully')

    return app


def _init_logging():
    global _logger
    _logger = getLogger('app')


def _init_config(flask_app: Flask):
    _logger.info('initiating configurations...')

    flask_app.config.from_mapping(config)


def _init_babel(flask_app: Flask):
    _logger.info('initiating babel...')

    global babel
    babel = Babel(flask_app)


def _init_db(flask_app: Flask):
    _logger.info('initiating database...')

    from .models import db
    db.init_app(flask_app)

    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import Column
    from sqlalchemy.sql.sqltypes import Enum as SQLEnum
    from sqlalchemy.sql.sqltypes import SchemaType

    def type_comparer(context: MigrationContext,
                      inspected_column: Column,
                      metadata_column: Column,
                      inspected_type: SchemaType,
                      metadata_type: SchemaType) -> Optional[bool]:

        _ = context, inspected_column, metadata_column
        if not (isinstance(inspected_type, SQLEnum)
                and isinstance(metadata_type, SQLEnum)):
            return None
        return set(inspected_type.enums) != set(metadata_type.enums)

    global migrate
    migrate = Migrate(flask_app, db, compare_type=type_comparer)


def _init_apis(flask_app: Flask):
    _logger.info('initiating APIs...')

    from app.api import init_app
    init_app(flask_app)


def _init_jinja(flask_app: Flask):
    _logger.info('initiating Jinja...')

    from flask_babel import gettext

    def get_year():
        import time
        return time.strftime('%Y')

    def get_time():
        import time
        return time.strftime('%Y-%m-%d %H:%M:%S')

    flask_app.jinja_env.globals['get_year'] = get_year
    flask_app.jinja_env.globals['get_time'] = get_time
    flask_app.jinja_env.globals['_'] = gettext
