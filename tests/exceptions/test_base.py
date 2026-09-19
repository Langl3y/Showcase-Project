import pytest

from app.api.common.responses import failure, success
from app.exceptions import (
    BreedDoesNotExist,
    FileDoesNotExist,
    ImageFormatError,
    InvalidArgument,
)
from app.exceptions.base import (
    ErrorWithResponseCode,
    MultipleErrors,
    _ErrorWithResponseCodeMeta,
)


def test_codes_are_allocated_per_domain():
    from app.exceptions import dog, file, user

    assert all(200 <= e.response_code < 300
               for e in (dog.BreedDoesNotExist, dog.DogImageDoesNotExist))
    assert all(300 <= e.response_code < 400
               for e in (file.FileDoesNotExist, file.ImageFormatError,
                         file.FileFormatError, file.FileTooBig,
                         file.FileNameTooLong))
    assert 100 <= user.UserDoesNotExist.response_code < 200


def test_every_code_is_unique():
    codes = list(_ErrorWithResponseCodeMeta.get_all_response_codes())
    assert len(codes) == len(set(codes))


def test_registering_a_duplicate_code_is_rejected():
    with pytest.raises(ValueError, match='already registered'):
        class Clashing(ErrorWithResponseCode):
            response_code = BreedDoesNotExist.response_code


def test_zero_is_not_a_valid_code():
    with pytest.raises(ValueError, match='non-zero'):
        class Zero(ErrorWithResponseCode):
            response_code = 0


def test_lookup_by_code():
    found = _ErrorWithResponseCodeMeta.response_code_to_class(
        BreedDoesNotExist.response_code)
    assert found is BreedDoesNotExist
    assert _ErrorWithResponseCodeMeta.response_code_to_class(987654) is None


def test_registry_describes_each_error():
    entry = _ErrorWithResponseCodeMeta.get_all_response_codes()[
        FileDoesNotExist.response_code]
    assert entry['class_name'] == 'FileDoesNotExist'
    assert entry['message_template'] == 'File does not exist'
    assert entry['module'].endswith('exceptions.file')


def test_scalar_payload_is_wrapped():
    err = BreedDoesNotExist(42)
    assert err.data == {'data': 42}
    assert err.code == 201


@pytest.mark.parametrize('payload, expected', [
    ({'id': 1}, {'id': 1}),
    ([1, 2], [1, 2]),
    (None, {}),
    (0, {}),
])
def test_payload_shapes(payload, expected):
    assert InvalidArgument(payload).data == expected


def test_explicit_message_wins_over_the_template():
    assert ImageFormatError(message='only png').message == 'only png'
    assert ImageFormatError().message.startswith('Only supports')


def test_template_interpolation_falls_back_when_keys_are_missing():
    class Interpolated(ErrorWithResponseCode):
        response_code = 987001
        message_template = '%(title)s failed for %(data)r'

    assert 'failed for' in Interpolated({'a': 1}).message

    class BadTemplate(ErrorWithResponseCode):
        response_code = 987002
        message_template = '%(nope)s'

    assert BadTemplate().message == '%(nope)s'


def test_repr_shows_type_and_message():
    text = repr(BreedDoesNotExist(1))
    assert 'BreedDoesNotExist' in text and 'Breed does not exist' in text


def test_multiple_errors_collects_each_one():
    err = MultipleErrors([BreedDoesNotExist(1), FileDoesNotExist(2)])
    assert err.code == 9999
    assert [d['code'] for d in err.data] == [201, 301]
    assert err.message == 'Multiple errors occurred'


def test_success_and_failure_envelopes():
    assert success() == {'code': 0, 'data': {}, 'message': 'Success'}
    assert success({'a': 1}, 'ok') == {'code': 0, 'data': {'a': 1}, 'message': 'ok'}
    assert failure(5) == {'code': 5, 'data': {}, 'message': 'Failure'}
    assert failure(5, 'bad', {'x': 1})['data'] == {'x': 1}


def test_failure_refuses_a_zero_code():
    with pytest.raises(ValueError, match='non-zero'):
        failure(0)
