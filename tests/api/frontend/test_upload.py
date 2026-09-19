import io
from unittest.mock import patch

import pytest

UPLOAD_URL = '/frontend/upload/image'

PNG = bytes.fromhex(
    '89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489'
    '0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082')
JPEG = bytes.fromhex(
    'ffd8ffe000104a46494600010100000100010000ffdb004300ffffffffffffffff'
    'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
    'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
    'ffffffffffffffffffffffffffffd9')


@pytest.fixture
def put_ok():
    with patch('app.api.frontend.upload.AWSBucket.put_file_with_acl',
               return_value=True) as put:
        yield put


@pytest.fixture
def auth(token):
    return {'AUTHORIZATION': token}


def _post(client, headers, data=PNG, filename='dog.png'):
    return client.post(UPLOAD_URL, headers=headers,
                       data={'img': (io.BytesIO(data), filename)},
                       content_type='multipart/form-data')


def test_requires_a_token(client):
    assert _post(client, {}).json['code'] != 0


def test_stores_the_file_and_returns_its_id(client, auth, put_ok):
    body = _post(client, auth).json

    assert body['code'] == 0
    assert body['data']['id']
    assert body['data']['file_url'].endswith('.png')


def test_passes_the_real_byte_length_to_minio(client, auth, put_ok):
    _post(client, auth)

    kwargs = put_ok.call_args.kwargs
    assert kwargs['length'] == len(PNG)
    assert kwargs['content_type'] == 'image/png'


def test_records_size_and_mime_on_the_file_row(client, auth, put_ok, app):
    from app.models import File

    file_id = _post(client, auth).json['data']['id']

    row = File.query.get(file_id)
    assert row.size == len(PNG)
    assert row.mime_type == File.MimeTypeEnum.ImagePng.value
    assert row.name == 'dog.png'


def test_detects_jpeg(client, auth, put_ok, app):
    from app.models import File

    body = _post(client, auth, data=JPEG, filename='dog.jpg').json

    assert body['code'] == 0
    assert File.query.get(body['data']['id']).mime_type == \
        File.MimeTypeEnum.ImageJpg.value


def test_rejects_a_missing_field(client, auth, put_ok):
    resp = client.post(UPLOAD_URL, headers=auth, data={},
                       content_type='multipart/form-data')
    assert resp.json['code'] != 0


def test_rejects_a_non_image(client, auth, put_ok):
    from app.exceptions import ImageFormatError

    body = _post(client, auth, data=b'%PDF-1.4 not an image',
                 filename='x.pdf').json
    assert body['code'] == ImageFormatError.response_code


def test_rejects_an_oversized_upload(client, auth, put_ok):
    from app.exceptions import FileTooBig

    big = PNG + b'\x00' * (10 * 1024 * 1024)
    body = _post(client, auth, data=big, filename='big.png').json
    assert body['code'] == FileTooBig.response_code


def test_rejects_a_long_filename(client, auth, put_ok):
    from app.exceptions import FileNameTooLong

    body = _post(client, auth, filename='n' * 140 + '.png').json
    assert body['code'] == FileNameTooLong.response_code


def test_reports_storage_failure(client, auth):
    from app.exceptions import ServiceUnavailable

    with patch('app.api.frontend.upload.AWSBucket.put_file_with_acl',
               return_value=False):
        body = _post(client, auth).json
    assert body['code'] == ServiceUnavailable.response_code


def test_nothing_is_persisted_when_storage_fails(client, auth, app):
    from app.models import File

    before = File.query.count()
    with patch('app.api.frontend.upload.AWSBucket.put_file_with_acl',
               return_value=False):
        _post(client, auth)
    assert File.query.count() == before
