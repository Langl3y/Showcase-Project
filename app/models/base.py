from enum import Enum
from logging import getLogger
from typing import Type, TypeVar

from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy
from sqlalchemy.orm import Session, scoped_session, sessionmaker

from app.utils.date_ import current_timestamp

_logger = getLogger(__name__)

T = TypeVar('T')


class DateTimeUTC:
    pass


class SQLAlchemy(_SQLAlchemy):
    session: Session

    def session_add_and_commit(self, obj: T) -> T:
        self.session.add(obj)
        self.session.commit()
        return obj


db = SQLAlchemy()


class _Session(Session):

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def new_session() -> _Session:
    return scoped_session(sessionmaker(class_=_Session, bind=db.engine))()


def row_to_dict(row, *,
                with_hook: bool = True,
                enum_to_name: bool = False):
    result = {(name := col.name):
              (v.name
               if isinstance(v := getattr(row, name), Enum) and enum_to_name
               else v)
              for col in type(row).__table__.columns}

    if with_hook:
        hook = getattr(row, '_row_to_dict_hook_', None)
        if hook is not None:
            try:
                hook(result)
            except Exception:
                pass

    return result


def get_primary_key(model: Type[db.Model]) -> str:
    from sqlalchemy.inspection import inspect as sql_inspect
    return sql_inspect(model).primary_key[0].name


class ModelBase(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)

    create_time = db.Column(db.Integer, default=current_timestamp, nullable=False)
    create_by = db.Column(db.String(64), nullable=False, default='')
    update_time = db.Column(db.Integer, default=current_timestamp, onupdate=current_timestamp, nullable=False)
    update_by = db.Column(db.String(64), nullable=False, default='')

    def to_dict(self, *, with_hook: bool = True, enum_to_name: bool = False):
        return row_to_dict(self, with_hook=with_hook,
                           enum_to_name=enum_to_name)

    @classmethod
    def get_or_create(cls, auto_commit=False, **kwargs) -> T:
        filters = [getattr(cls, k) == v for k, v in kwargs.items()]
        if record := cls.query.filter(*filters).first():
            return record
        record = cls()
        for k, v in kwargs.items():
            setattr(record, k, v)
        if auto_commit:
            return db.session_add_and_commit(record)
        return record


__all__ = 'db', 'new_session', 'row_to_dict', 'get_primary_key', 'ModelBase'
