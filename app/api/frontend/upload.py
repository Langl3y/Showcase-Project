import imghdr
import os

from flask import g, request
from flask_restx import reqparse
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from app.api.common import Namespace, Resource
from app.utils import AWSBucket, new_file_key

from ...exceptions import (
    FileNameTooLong,
    FileTooBig,
    ImageFormatError,
    InvalidArgument,
    ServiceUnavailable,
)
from ...models import File, db
from ..common.decorators import require_login, respond_with_code

ns = Namespace('Upload')

image_parser = reqparse.RequestParser()
image_parser.add_argument('img', type=FileStorage, location='files',
                          required=True, help='png/jpg image, max 10MB')


@ns.route('/image')
@respond_with_code
class ImageUploadResource(Resource):
    @classmethod
    @require_login
    @ns.expect(image_parser)
    def post(cls):
        img = request.files.get('img')
        if not img:
            raise InvalidArgument('img')

        if (img_type := imghdr.what(img)) not in {'png', 'jpeg', 'jpg'}:
            raise ImageFormatError

        if int(request.headers['CONTENT_LENGTH']) > 1024 * 1024 * 10:
            raise FileTooBig

        mime_type = File.MimeTypeEnum.ImagePng if img_type == 'png' \
            else File.MimeTypeEnum.ImageJpg

        img.seek(0, os.SEEK_END)
        length = img.tell()
        img.seek(0)

        file_key = new_file_key(suffix=img_type)
        if not AWSBucket.put_file_with_acl(
                file_key, img, AWSBucket.ACLEnum.PRIVATE,
                length=length, content_type=f'image/{img_type}'):
            raise ServiceUnavailable
        url = AWSBucket.get_static_file_url(file_key)

        filename = secure_filename(img.filename)
        if len(filename) > 128:
            raise FileNameTooLong

        new_file: File = File.new(
            g.user.id, file_key,
            filename,
            size=length,
            mime_type=mime_type
        )

        db.session.add(new_file)
        db.session.commit()

        return {
            'file_url': url,
            'id': new_file.id
        }
