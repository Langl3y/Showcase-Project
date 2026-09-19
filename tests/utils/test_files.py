import io
from unittest.mock import MagicMock

import pytest
from minio.error import S3Error

from app.utils.files import _MinIOBucket


def _s3_error():
    return S3Error('NoSuchBucket', 'missing', 'res', 'rid', 'hid', 'resp')


@pytest.fixture
def bucket():
    b = _MinIOBucket(endpoint='127.0.0.1:9000', access_key='k', secret_key='s',
                     bucket_name='test-bucket', secure=False)
    b._client = MagicMock()
    return b


def test_exposes_its_name_and_client(bucket):
    assert bucket.bucket_name == 'test-bucket'
    assert bucket.client is bucket._client


def test_ensure_bucket_creates_only_when_absent(bucket):
    bucket._client.bucket_exists.return_value = True
    assert bucket.ensure_bucket() is True
    bucket._client.make_bucket.assert_not_called()

    bucket._client.bucket_exists.return_value = False
    assert bucket.ensure_bucket() is True
    bucket._client.make_bucket.assert_called_once_with('test-bucket')


def test_put_file_passes_length_and_content_type(bucket):
    data = io.BytesIO(b'abc')
    assert bucket.put_file('k.png', data, 3, content_type='image/png') is True

    _, args, kwargs = bucket._client.put_object.mock_calls[0]
    assert args[0] == 'test-bucket'
    assert args[1] == 'k.png'
    assert args[3] == 3
    assert kwargs['content_type'] == 'image/png'


def test_put_file_reports_failure_instead_of_raising(bucket):
    bucket._client.put_object.side_effect = _s3_error()
    assert bucket.put_file('k.png', io.BytesIO(b'abc'), 3) is False


def test_put_file_with_acl_sets_the_acl_metadata(bucket):
    assert bucket.put_file_with_acl(
        'k.png', io.BytesIO(b'abc'), _MinIOBucket.ACLEnum.PRIVATE, length=3) is True
    kwargs = bucket._client.put_object.mock_calls[0].kwargs
    assert kwargs['metadata']['x-amz-acl'] == 'private'


def test_put_file_with_acl_accepts_a_plain_string(bucket):
    assert bucket.put_file_with_acl('k.png', io.BytesIO(b'a'), 'PUBLIC_READ',
                                    length=1) is True
    kwargs = bucket._client.put_object.mock_calls[0].kwargs
    assert kwargs['metadata']['x-amz-acl'] == 'public_read'


def test_put_file_with_acl_reports_failure(bucket):
    bucket._client.put_object.side_effect = _s3_error()
    assert bucket.put_file_with_acl('k', io.BytesIO(b'a'),
                                    _MinIOBucket.ACLEnum.PRIVATE, length=1) is False


def test_delete_file(bucket):
    assert bucket.delete_file('k.png') is True
    bucket._client.remove_object.assert_called_once_with('test-bucket', 'k.png')

    bucket._client.remove_object.side_effect = _s3_error()
    assert bucket.delete_file('k.png') is False


def test_static_url_prefers_the_configured_public_base(bucket):
    url = bucket.get_static_file_url('breed_images/a.png')
    assert url.endswith('/breed_images/a.png')
    assert url.startswith('http://')


def test_static_url_falls_back_to_the_endpoint(bucket, monkeypatch):
    monkeypatch.setitem(__import__('app.config', fromlist=['config']).config,
                        'UPLOAD_STATIC_URL', '')
    assert bucket.get_static_file_url('a.png') == \
        'http://127.0.0.1:9000/test-bucket/a.png'


def test_private_urls_are_presigned(bucket):
    bucket._client.presigned_get_object.return_value = 'http://signed/get'
    bucket._client.presigned_put_object.return_value = 'http://signed/put'

    assert bucket.get_private_file_url('a.png') == 'http://signed/get'
    assert bucket.put_private_url('a.png') == 'http://signed/put'
    assert bucket._client.presigned_put_object.mock_calls[0].kwargs['expires']
