from .base import ErrorWithResponseCode


class _InvalidArgument(ErrorWithResponseCode):
    response_code = 10000


class InvalidTimestamp(_InvalidArgument):
    response_code = 10001


class InvalidPageNum(_InvalidArgument):
    response_code = 10002


class InvalidPageSize(_InvalidArgument):
    response_code = 10003


class InvalidUserID(_InvalidArgument):
    response_code = 10009


class InvalidStatus(_InvalidArgument):
    response_code = 10010


class InvalidAmount(_InvalidArgument):
    response_code = 10016


class InvalidString(_InvalidArgument):
    response_code = 10017


class InvalidFormat(_InvalidArgument):
    response_code = 10018


class InvalidPlatform(_InvalidArgument):
    response_code = 10015
