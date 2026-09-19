from flask import g
from flask_restx import fields as fx_fields, marshal
from webargs import fields

from app.models import Breed
from ..common import Namespace, Resource, respond_with_code, require_login

ns = Namespace('Dog')


@ns.route('/breed')
@respond_with_code
class ListBreed(Resource):
    @classmethod
    @require_login
    @ns.use_kwargs(dict(
        page=fields.Integer(missing=1),
        limit=fields.Integer(missing=50)
    ))
    def get(cls, **kwargs):
        objs = Breed.query.with_entities(Breed.id, Breed.name).order_by(Breed.id.asc())
        records = objs.paginate(page=kwargs["page"], per_page=kwargs["limit"], error_out=False)
        return {
            "items": list(map(cls.to_dict, records.items)),
            "page": records.page,
            "limit": records.per_page,
            "total": records.total,
            "pages": records.pages,
            "has_next": records.has_next,
        }

    @classmethod
    def to_dict(cls, obj: Breed):
        return dict(
            id=obj.id,
            name=obj.name,
        )
