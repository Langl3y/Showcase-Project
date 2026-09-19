from enum import Enum
from re import compile as re_compile
from typing import IO, Union

from minio import Minio
from minio.error import S3Error

from ..config import config


class _MinIOBucket:

    DEFAULT_TTL = 3600

    class ACLEnum(Enum):
        PRIVATE = "PRIVATE"
        PUBLIC_READ = "PUBLIC_READ"

    _RE_FILE_URL = re_compile(
        r'(?P<scheme>https?://)(?P<host>[^/]+)/(?P<bucket>[^/]+)/(?P<path>.*)')

    def __init__(self,
                 endpoint: str,
                 access_key: str,
                 secret_key: str,
                 bucket_name: str,
                 region_name: str = 'us-east-1',
                 secure: bool = True):
        self._endpoint = endpoint
        self._bucket_name = bucket_name
        self._region_name = region_name
        self._secure = secure
        self._client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region_name,
        )

    @property
    def bucket_name(self):
        return self._bucket_name

    @property
    def client(self) -> Minio:
        return self._client

    def ensure_bucket(self) -> bool:
        found = self._client.bucket_exists(self._bucket_name)
        if not found:
            self._client.make_bucket(self._bucket_name)
        return True

    def get_private_file_url(self, key: str) -> str:
        return self._client.presigned_get_object(
            self._bucket_name,
            key,
        )

    def put_private_url(self, key: str) -> str:
        from datetime import timedelta
        return self._client.presigned_put_object(
            self._bucket_name,
            key,
            expires=timedelta(seconds=self.DEFAULT_TTL),
        )

    def get_static_file_url(self, key: str) -> str:
        scheme = 'https' if self._secure else 'http'
        static_base = config.get('UPLOAD_STATIC_URL', '')
        if static_base:
            return f"{static_base.rstrip('/')}/{key.lstrip('/')}"
        return f'{scheme}://{self._endpoint}/{self._bucket_name}/{key}'

    def put_file(self, key: str, file: IO, length: int = 0,
                 content_type: str = 'application/octet-stream') -> bool:
        try:
            self._client.put_object(
                self._bucket_name, key, file, length,
                content_type=content_type,
            )
            return True
        except S3Error:
            return False

    def put_file_with_acl(self, key: str, file: IO,
                          acl: Union[str, ACLEnum],
                          length: int = 0,
                          content_type: str = 'application/octet-stream',
                          **kwargs) -> bool:
        if isinstance(acl, self.ACLEnum):
            acl = acl.value
        metadata = kwargs.pop('metadata', {}) or {}
        metadata.setdefault('x-amz-acl', acl.lower() if isinstance(acl, str) else acl)
        try:
            self._client.put_object(
                self._bucket_name, key, file, length,
                content_type=content_type,
                metadata=metadata,
                **kwargs,
            )
            return True
        except S3Error:
            return False

    def delete_file(self, key: str) -> bool:
        try:
            self._client.remove_object(self._bucket_name, key)
            return True
        except S3Error:
            return False


_minio_config = config['MINIO_FILE']

MinioDefaultBucket = _MinIOBucket(
    endpoint=_minio_config['endpoint'],
    access_key=_minio_config['access_key'],
    secret_key=_minio_config['secret_key'],
    bucket_name=_minio_config['bucket_name'],
    region_name=_minio_config.get('region_name', 'us-east-1'),
    secure=_minio_config.get('secure', False),
)

# Substitute for AWS S3
AWSBucket = MinioDefaultBucket
