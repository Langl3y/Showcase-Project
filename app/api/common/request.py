from enum import Enum
from typing import Callable, Optional

from flask import request, g

from app.exceptions import (
    InvalidPlatform, InvalidArgument, UnAuthorization
)
from app.common import LanguageEnum
from app.models import User
from app.utils.chicken_ribs import NamedObject
from app.utils.date_ import now

_EMPTY = NamedObject('Empty')


class RequestPlatform(Enum):

    WEB = 'WEB'
    iOS = 'iOS'
    ANDROID = 'Android'
    UNKNOWN = 'UNKNOWN'

    def is_web(self):
        return self is self.WEB

    def is_ios(self):
        return self is self.iOS

    def is_android(self):
        return self is self.ANDROID

    def is_mobile(self):
        return self.is_ios() or self.is_android()

    @classmethod
    def from_request(cls) -> 'RequestPlatform':
        platform = request.headers.get('PLATFORM', '')
        if platform:
            try:
                platform = RequestPlatform(platform)
            except ValueError:
                raise InvalidPlatform(platform)
            if platform is cls.UNKNOWN:
                raise InvalidPlatform(platform)
        else:
            platform = cls.UNKNOWN
        return platform


def get_request_ip() -> str:
    return request.remote_addr or '127.0.0.1'


def get_request_platform() -> RequestPlatform:
    return RequestPlatform.from_request()


def get_request_language() -> LanguageEnum:
    lang = request.headers.get('Accept-Language', 'en_US')
    try:
        return LanguageEnum(lang)
    except ValueError:
        return LanguageEnum.en_US


def get_request_user_agent() -> str:
    return request.user_agent.string or ''


def get_request_data() -> dict:
    return dict(request.args or request.json or ())


def get_request_info() -> dict:
    return dict(
        path=request.path,
        method=request.method,
        ip=get_request_ip(),
        platform=get_request_platform().name,
        language=get_request_language().name,
        data=get_request_data(),
        request_time=now()
    )


def get_request_user() -> Optional[User]:
    return getattr(g, 'user', None)
