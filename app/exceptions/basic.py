from .base import ErrorWithResponseCode


class CommonError(ErrorWithResponseCode):
    response_code = 1
    message_template = 'Error'


class InvalidArgument(ErrorWithResponseCode):
    response_code = 2
    message_template = 'Invalid argument'


class InternalServerError(ErrorWithResponseCode):
    response_code = 3
    message_template = 'Internal error'


class UnAuthorization(ErrorWithResponseCode):
    response_code = 401
    message_template = 'Unauthorized'


class Forbidden(ErrorWithResponseCode):
    response_code = 403
    message_template = 'Forbidden'


class NotFound(ErrorWithResponseCode):
    response_code = 404
    message_template = 'Not found'


class ServiceUnavailable(ErrorWithResponseCode):
    response_code = 35
    message_template = 'Service Unavailable'


class FrequencyExceeded(ErrorWithResponseCode):
    response_code = 213
    message_template = "Please don't try too frequently"


class AlreadyExists(ErrorWithResponseCode):
    response_code = 5005
    message_template = 'Already exists'


class AmountLimitExceeded(ErrorWithResponseCode):
    response_code = 5003
    message_template = 'Amount limit exceeded'


class InvalidVerificationCode(ErrorWithResponseCode):
    response_code = 7
    message_template = 'Verification code error'


class TwoFactorAuthenticationFailed(ErrorWithResponseCode):
    response_code = 8
    message_template = '2FA code protect operate error'
