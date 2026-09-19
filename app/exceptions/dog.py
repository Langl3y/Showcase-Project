from .base import ErrorWithResponseCode


class BreedDoesNotExist(ErrorWithResponseCode):
    response_code = 201
    message_template = 'Breed does not exist'
