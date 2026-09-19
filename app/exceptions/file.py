from .base import ErrorWithResponseCode


class ImageFormatError(ErrorWithResponseCode):
    response_code = 11
    message_template = 'Only supports upload png/jpg/jpeg/bmp/gif image format.'


class FileFormatError(ErrorWithResponseCode):
    response_code = 12
    message_template = 'File format is not supported.'


class FileTooBig(ErrorWithResponseCode):
    response_code = 950
    message_template = 'File is too big'


class FileNameTooLong(ErrorWithResponseCode):
    response_code = 3613
    message_template = 'File name is too long'
