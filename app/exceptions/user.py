from .base import ErrorWithResponseCode


class InvalidUsernameOrPassword(ErrorWithResponseCode):
    response_code = 101
    message_template = 'Invalid username or password'


class EmailAlreadyExists(ErrorWithResponseCode):
    response_code = 102
    message_template = 'Email already registered'


class EmailDoesNotExist(ErrorWithResponseCode):
    response_code = 103
    message_template = 'Email does not exist'


class MobileAlreadyExists(ErrorWithResponseCode):
    response_code = 104
    message_template = 'Mobile already registered'


class MobileDoesNotExist(ErrorWithResponseCode):
    response_code = 105
    message_template = 'Mobile does not exist'


class UserDoesNotExist(ErrorWithResponseCode):
    response_code = 106
    message_template = 'User does not exist'


class UsernameAlreadyExists(ErrorWithResponseCode):
    response_code = 107
    message_template = 'Username already exists'


class EmailAlreadyBound(ErrorWithResponseCode):
    response_code = 108
    message_template = 'Email already bound'


class MobileAlreadyBound(ErrorWithResponseCode):
    response_code = 109
    message_template = 'Mobile already bound'


class AccountFrozen(ErrorWithResponseCode):
    response_code = 110
    message_template = 'Account is frozen'


class AccountDeleted(ErrorWithResponseCode):
    response_code = 111
    message_template = 'Account is deleted'


class PasswordDoesNotMatch(ErrorWithResponseCode):
    response_code = 112
    message_template = 'Password does not match'


class InvalidPassword(ErrorWithResponseCode):
    response_code = 113
    message_template = 'Invalid password'
