from .base import ErrorWithResponseCode


class BreedDoesNotExist(ErrorWithResponseCode):
    response_code = 201
    message_template = 'Breed does not exist'


class DogImageDoesNotExist(ErrorWithResponseCode):
    response_code = 202
    message_template = 'Dog image does not exist'
