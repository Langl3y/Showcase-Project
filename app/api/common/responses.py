from typing import Any

from app.utils.chicken_ribs import NamedObject


_EMPTY = NamedObject('Empty')


def success(data: Any = _EMPTY, message: str = 'Success'):
    if data is _EMPTY:
        data = {}
    return dict(
        code=0,
        data=data,
        message=message
    )


def failure(code: int, message='Failure', data: Any = _EMPTY):
    if not code:
        raise ValueError('`code` must be non-zero')
    if data is _EMPTY:
        data = {}
    return dict(
        code=code,
        data=data,
        message=message
    )
