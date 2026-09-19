from flask import g
from flask_restx import fields as fx_fields, marshal
from webargs import fields

from app.exceptions import BreedDoesNotExist
from app.models import Breed
from ..common import Namespace, Resource, respond_with_code, require_login, extra_fields

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


@ns.route('/breed/<int:_id>')
@respond_with_code
class BreedDetail(Resource):
    @classmethod
    @require_login
    @ns.use_kwargs(dict(
        measurement=extra_fields.EnumField(
            Breed.MeasurementEnum, missing=Breed.MeasurementEnum.Metric),
    ))
    def get(cls, _id, **kwargs):
        obj = Breed.query.get(_id)
        if not obj:
            raise BreedDoesNotExist(_id)

        measurement = kwargs.get('measurement') or Breed.MeasurementEnum.Metric
        imperial = measurement is Breed.MeasurementEnum.Imperial

        result = cls.to_dict(obj)
        result.update(
            measurement=measurement.value,
            weight=obj.weight_imperial if imperial else obj.weight_metric,
            height=obj.height_imperial if imperial else obj.height_metric,
        )
        return result

    @classmethod
    def to_dict(cls, obj: Breed):
        return dict(
            id=obj.id,
            name=obj.name,
            species_id=obj.species_id,
            life_span=obj.life_span,
            temperament=obj.temperament,
            origin=obj.origin,
            country_code=obj.country_code,
            country_codes=obj.country_codes,
            description=obj.description,
            bred_for=obj.bred_for,
            perfect_for=obj.perfect_for,
            breed_group=obj.breed_group,
            history=obj.history,
            image=obj.to_dict().get('image'),
            status=obj.status.value,
            create_time=obj.create_time,
            update_time=obj.update_time,
        )
