from typing import Optional
from enum import Enum

from .base import db, ModelBase
from ..utils import MinioDefaultBucket
from ..config import config


_default_bucket_name = config['MINIO_FILE']['bucket_name']


class File(ModelBase):
    class ProviderEnum(Enum):
        Minio = 'Minio'

    class MimeTypeEnum(Enum):
        File = 'File'
        ImagePng = 'ImagePng'
        ImageJpg = 'ImageJpg'
        ImageJpeg = 'ImageJpeg'
        ImageGif = 'ImageGif'
        ImageWebp = 'ImageWebp'
        VideoMp4 = 'VideoMp4'
        VideoMov = 'VideoMov'
        VideoAvi = 'VideoAvi'
        DocumentPdf = 'DocumentPdf'
        DocumentDoc = 'DocumentDoc'
        DocumentDocx = 'DocumentDocx'
        DocumentXls = 'DocumentXls'
        DocumentXlsx = 'DocumentXlsx'
        AudioMp3 = 'AudioMp3'

    class ACLEnum(Enum):
        PRIVATE = "Private"
        PUBLIC_READ = "PublicRead"

    class StatusEnum(Enum):
        Valid = 'Valid'
        Invalid = 'Invalid'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    bucket = db.Column(db.String(64), nullable=False, default=_default_bucket_name)
    key = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(256), nullable=False, default='')
    size = db.Column(db.Integer, nullable=False, default=0)
    extra = db.Column(db.Text)

    provider = db.Column(db.Enum(ProviderEnum), nullable=False, default=ProviderEnum.Minio)
    mime_type = db.Column(db.String(64), nullable=False, default=MimeTypeEnum.File.value)
    acl = db.Column(db.Enum(ACLEnum), nullable=False, default=ACLEnum.PUBLIC_READ)
    status = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.Valid, index=True)

    width = db.Column(db.Integer, nullable=True)
    height = db.Column(db.Integer, nullable=True)

    user = db.relationship('User', backref=db.backref('files', lazy='dynamic'))

    @property
    def bucket_map(self) -> dict:
        return {
            _default_bucket_name: MinioDefaultBucket,
        }

    @property
    def _bucket_handler(self):
        return self.bucket_map[self.bucket]

    @property
    def all_data(self) -> dict:
        return {
            'id': self.id,
            'file_name': self.name,
            'file': self.private_url,
            'file_type': self.mime_type,
            'size': self.size,
            'width': self.width,
            'height': self.height,
        }

    @property
    def static_url(self) -> str:
        handler = self._bucket_handler
        if self.provider == self.ProviderEnum.Minio:
            return handler.get_static_file_url(self.key)
        return ''

    @property
    def private_url(self) -> str:
        handler = self._bucket_handler
        if self.provider == self.ProviderEnum.Minio:
            return handler.get_private_file_url(self.key)
        return ''

    def _row_to_dict_hook_(self, result: dict):
        result['static_url'] = self.static_url
        result['private_url'] = self.private_url

    @classmethod
    def new(cls,
            user_id: Optional[int],
            key: str,
            name: str,
            size: int = 0,
            extra: str = None,
            mime_type: MimeTypeEnum | str = 'File',
            acl: ACLEnum = ACLEnum.PUBLIC_READ,
            provider: ProviderEnum = ProviderEnum.Minio,
            bucket: str = _default_bucket_name,
            width: Optional[int] = None,
            height: Optional[int] = None):
        if isinstance(mime_type, cls.MimeTypeEnum):
            mime_type = mime_type.value

        if provider != cls.ProviderEnum.Minio:
            raise ValueError(f'Unsupported provider: {provider}')

        return cls(
            user_id=user_id,
            bucket=bucket,
            key=key,
            name=name,
            size=size,
            extra=extra,
            mime_type=mime_type,
            provider=provider,
            acl=acl,
            width=width,
            height=height,
        )
