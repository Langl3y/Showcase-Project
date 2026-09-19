from functools import wraps
from inspect import isclass
from typing import Callable

from flask import current_app, g, request, Response
from flask.views import http_method_funcs as _http_method_funcs

from app.models import User
from app.exceptions import UnAuthorization
from app.caches import AuthCache
from .responses import success, failure


def _decorate_class(dec: Callable, cls):
    cls_vars = vars(cls)
    for name in _http_method_funcs:
        func = cls_vars.get(name)
        if func is None:
            continue
        if isinstance(func, (classmethod, staticmethod)):
            func = type(func)(respond_with_code(func.__func__))
        else:
            func = dec(func)
        setattr(cls, name, func)
    return cls


def respond_with_code(func_or_class):
    if isclass(func_or_class):
        return _decorate_class(respond_with_code, func_or_class)

    @wraps(func_or_class)
    def wrapper(*args, **kwargs):
        if current_app.config.get('DEBUG'):
            resp = func_or_class(*args, **kwargs)
        else:
            try:
                resp = func_or_class(*args, **kwargs)
            except Exception as exc:
                message_raw = str(repr(exc))
                return failure(
                    code=400,
                    message=message_raw
                )
        if isinstance(resp, Response):
            return resp
        return success(resp)

    return wrapper


def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('AUTHORIZATION', '')
        if not auth_header:
            raise UnAuthorization('Missing authorization token')

        token = auth_header.replace('Bearer ', '').strip()
        user_id = AuthCache(token).get_user_id()

        if not user_id:
            raise UnAuthorization('Invalid or expired token')

        user = User.query.get(user_id)
        if not user:
            raise UnAuthorization('User not found')

        if user.status != User.StatusEnum.Valid:
            raise UnAuthorization('Account is not active')

        g.user = user
        g.user_id = user_id
        g.auth_token = token
        return func(*args, **kwargs)

    return wrapper
