import json
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from enum import Enum, EnumMeta
from json import JSONEncoder as _JSONEncoder
from traceback import format_exc
from typing import Dict, Type, Union

import marshmallow as ma
from dateutil.tz import UTC
from flask import Response, current_app, request
from flask_restx import Api as _Api
from flask_restx import Namespace as _Namespace
from flask_restx import Resource as _Resource
from flask_restx import fields as restx_fields
from flask_restx.utils import unpack
from marshmallow import fields as mm_fields
from marshmallow.utils import EXCLUDE
from sqlalchemy.exc import DataError, IntegrityError
from webargs.flaskparser import parser, use_kwargs
from werkzeug.exceptions import HTTPException

from app.exceptions import (
    AlreadyExists,
    AmountLimitExceeded,
    ErrorWithResponseCode,
    InvalidArgument,
    ServiceUnavailable,
)
from app.models import db, row_to_dict
from app.utils.text import remove_suffix

from .responses import failure


@parser.error_handler
def handle_request_parsing_error(err, req, schema,
                                 *, error_status_code, error_headers):
    raise InvalidArgument(err.messages)


class Api(_Api):

    def handle_error(self, e):
        if isinstance(e, ErrorWithResponseCode):
            return Response(json.dumps(
                failure(e.response_code, e.message, e.data),
                cls=JsonEncoder
            ), mimetype='application/json')

        elif isinstance(e, HTTPException):
            data = getattr(e, 'data', {'message': e.description, 'errors': ''})
            return Response(json.dumps(
                failure(e.code, data['message'], data['errors']),
                cls=JsonEncoder
            ), mimetype='application/json')

        elif isinstance(e, DataError):
            if hasattr(e.orig, 'args') and e.orig.args[0] == 1264:
                return Response(json.dumps(
                    failure(AmountLimitExceeded.response_code,
                            AmountLimitExceeded.message_template,
                            {}),
                    cls=JsonEncoder
                ), mimetype='application/json')

        elif isinstance(e, IntegrityError):
            if hasattr(e.orig, 'args') and e.orig.args[0] == 1062:
                return Response(json.dumps(
                    failure(AlreadyExists.response_code,
                            AlreadyExists.message_template,
                            {}),
                    cls=JsonEncoder
                ), mimetype='application/json')

        else:
            print(format_exc())
            current_app.logger.error(format_exc())
            return Response(json.dumps(
                failure(ServiceUnavailable.response_code,
                        ServiceUnavailable.message_template,
                        {}),
                cls=JsonEncoder
            ), mimetype='application/json')


class Resource(_Resource):

    def dispatch_request(self, *args, **kwargs):
        meth = getattr(self, request.method.lower(), None)
        if meth is None and request.method == "HEAD":
            meth = getattr(self, "get", None)
        assert meth is not None, "Unimplemented method %r" % request.method

        if isinstance(self.method_decorators, Mapping):
            decorators = self.method_decorators.get(request.method.lower(), [])
        else:
            decorators = self.method_decorators

        for decorator in decorators:
            meth = decorator(meth)

        self.validate_payload(meth)

        resp = meth(*args, **kwargs)

        if isinstance(resp, Response):
            return resp

        representations = self.representations or {}

        media_type = request.accept_mimetypes.best_match(
            representations, default=None)
        if media_type in representations:
            data, code, headers = unpack(resp)
            resp = representations[media_type](data, code, headers)
            resp.headers["Content-Type"] = media_type
            return resp

        return resp


class Namespace(_Namespace):

    _METHODS_WITH_BODY = frozenset(['post', 'put', 'patch'])

    def use_kwargs(self, fields: Dict[str,
                                      Union[mm_fields.Field,
                                            Type[mm_fields.Field]]]):
        def validate_field(_f):
            if isinstance(_f, mm_fields.Field):
                return _f
            if isinstance(_f, type) and issubclass(_f, mm_fields.Field):
                return _f()
            raise TypeError(f'invalid field: {_f}')
        fields = {key: validate_field(field) for key, field in fields.items()}

        def field_desc(_key: str, _field: mm_fields.Field):
            _texts = []
            if _desc := _field.metadata.get('desc'):
                _texts.append(_desc)
            if (_default := _field.missing) is not mm_fields.missing_:
                _texts.append(f'default={_default!r}')
            return ', '.join(_texts)

        def map_restx_field(_field: mm_fields.Field) -> restx_fields.Raw:
            if isinstance(_field, mm_fields.Boolean):
                _field_cls = restx_fields.Boolean
            elif isinstance(_field, mm_fields.Integer):
                _field_cls = restx_fields.Integer
            elif isinstance(_field, mm_fields.Number):
                _field_cls = restx_fields.Arbitrary
            else:
                _field_cls = restx_fields.String
            if (_example := _field.metadata.get('example')) is None \
                and (_example := _field.missing) is mm_fields.missing_:
                _example = None
            return _field_cls(required=_field.required, example=_example)

        def dec(func):
            if (func_name := func.__name__) in self._METHODS_WITH_BODY:
                model_name = ''.join([
                    self.name.replace(' ', ''),
                    remove_suffix(func.__qualname__.split('.')[-2],
                                  'Resource'),
                    func_name.capitalize(),
                    'Request'
                ])
                model = self.model(model_name,
                                   {key: map_restx_field(field)
                                    for key, field in fields.items()})
                func = self.expect(model)(func)
                location = 'json'

            else:
                for _key, field in fields.items():
                    if field.required:
                        continue
                    if field.default is mm_fields.missing_:
                        field.default = None

                def swagger_type(_field):
                    if isinstance(_field, mm_fields.Boolean):
                        return 'boolean'
                    if isinstance(_field, mm_fields.Integer):
                        return 'integer'
                    if isinstance(_field, mm_fields.Number):
                        return 'number'
                    return 'string'

                func = self.doc(params={
                    key: {
                        'in': 'query',
                        'type': swagger_type(field),
                        'description': field_desc(key, field),
                        'required': field.required
                    } for key, field in fields.items()
                })(func)
                location = 'query'
            argmap = ma.Schema.from_dict(fields)(unknown=EXCLUDE)
            return use_kwargs(argmap, location=location)(func)

        return dec


class JsonEncoder(_JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, datetime):
            return int(obj.timestamp())
        if isinstance(obj, date):
            dt = datetime(obj.year, obj.month, obj.day, tzinfo=UTC)
            return int(dt.timestamp())
        if isinstance(obj, Decimal):
            return f'{obj.normalize():f}'
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, EnumMeta):
            return {e.name: e.value for e in obj}
        if isinstance(obj, db.Model):
            return row_to_dict(obj, enum_to_name=True)
        return _JSONEncoder.default(self, obj)
