from .base import ErrorWithResponseCode


class FileDoesNotExist(ErrorWithResponseCode):
    response_code = 301
    message_template = 'File does not exist'


class ImageFormatError(ErrorWithResponseCode):
    response_code = 302
    message_template = 'Only supports upload png/jpg/jpeg/bmp/gif image format.'


class FileFormatError(ErrorWithResponseCode):
    response_code = 303
    message_template = 'File format is not supported.'


class FileTooBig(ErrorWithResponseCode):
    response_code = 304
    message_template = 'File is too big'


class FileNameTooLong(ErrorWithResponseCode):
    response_code = 305
    message_template = 'File name is too long'
