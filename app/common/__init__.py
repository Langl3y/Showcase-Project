from enum import Enum


class LanguageEnum(Enum):
    en_US = 'en_US'
    zh_CN = 'zh_CN'


LOGIN_TOKEN_SIZE = 32
LOGIN_STATE_DEFAULT_TTL = 60 * 60 * 24 * 7

WEB_DEFAULT_PAGE = 1
WEB_DEFAULT_LIMIT = 20
