from webargs import fields
from flask import g

from app.exceptions import (BreedDoesNotExist, DogImageDoesNotExist,
                            FileDoesNotExist, ImageFormatError)
from app.models import Breed, DogImage, File, BreedImage, db
from ..common import Namespace, Resource, respond_with_code, require_login, extra_fields

ns = Namespace('Dog')


IMAGE_MIME_TYPES = frozenset({
    File.MimeTypeEnum.ImagePng.value,
    File.MimeTypeEnum.ImageJpg.value,
    File.MimeTypeEnum.ImageJpeg.value,
    File.MimeTypeEnum.ImageGif.value,
    File.MimeTypeEnum.ImageWebp.value,
})


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


@ns.route('/breed/image')
@respond_with_code
class BreedImageAssociate(Resource):
    @classmethod
    @require_login
    @ns.use_kwargs(dict(
        file_id=fields.Integer(required=True),
        breed_id=fields.Integer(required=True),
    ))
    def post(cls, **kwargs):
        file_id = kwargs.get('file_id')
        breed_id = kwargs.get('breed_id')

        file = File.query.filter(
            File.id == file_id,
            File.status == File.StatusEnum.Valid
        ).first()

        if file is None:
            raise FileDoesNotExist(file_id)
        if file.mime_type not in IMAGE_MIME_TYPES:
            raise ImageFormatError

        breed: Breed = Breed.query.get(breed_id)
        if breed is None:
            raise BreedDoesNotExist(breed_id)

        current = breed.image_obj
        if current is not None and current.file_id == file.id:
            return cls.to_dict(breed, current)

        new_breed_img = BreedImage(file_id=file.id)
        db.session.add(new_breed_img)
        db.session.flush()

        if current is not None:
            current.status = BreedImage.StatusEnum.Deleted

        breed.image_id = new_breed_img.id
        breed.reference_image_id = None
        db.session.commit()

        return cls.to_dict(breed, new_breed_img)

    @classmethod
    def to_dict(cls, breed: Breed, image: BreedImage):
        return dict(
            breed_id=breed.id,
            image_id=image.id,
            file_id=image.file_id,
            url=image.static_url,
        )


@ns.route('/image')
@respond_with_code
class DogImageCreate(Resource):
    @classmethod
    @require_login
    @ns.use_kwargs(dict(
        file_id=fields.Integer(required=True),
        breed_id=fields.Integer(required=True),
        title=fields.String(missing=''),
    ))
    def post(cls, **kwargs):
        file_id = kwargs.get('file_id')
        breed_id = kwargs.get('breed_id')
        title = (kwargs.get('title') or '').strip()

        file = File.query.filter(
            File.id == file_id,
            File.status == File.StatusEnum.Valid
        ).first()

        if file is None:
            raise FileDoesNotExist(file_id)
        if file.mime_type not in IMAGE_MIME_TYPES:
            raise ImageFormatError

        breed = Breed.query.get(breed_id)
        if breed is None:
            raise BreedDoesNotExist(breed_id)

        user = g.user
        existing = DogImage.query.filter(
            DogImage.user_id == user.id,
            DogImage.breed_id == breed.id,
            DogImage.file_id == file.id,
            DogImage.status == DogImage.StatusEnum.Valid,
        ).first()

        if existing is not None:
            return cls.to_dict(existing)

        obj = DogImage(
            breed_id=breed.id,
            file_id=file.id,
            user_id=user.id,
            title=title,
        )
        db.session.add(obj)
        db.session.flush()
        db.session.commit()

        return cls.to_dict(obj)

    @classmethod
    def to_dict(cls, obj: DogImage):
        return dict(
            id=obj.id,
            breed_id=obj.breed_id,
            file_id=obj.file_id,
            user_id=obj.user_id,
            url=obj.static_url,
            title=obj.title,
            status=obj.status.value,
            create_time=obj.create_time,
            width=obj.width,
            height=obj.height,
        )


@ns.route('/recent/images')
@respond_with_code
class ListDogImage(Resource):
    @classmethod
    @require_login
    @ns.use_kwargs(dict(
        page=fields.Integer(missing=1),
        limit=fields.Integer(missing=50),
        breed_id=fields.Integer(missing=None),
        user_id=fields.Integer(missing=None),
    ))
    def get(cls, **kwargs):
        query = DogImage.query.filter(DogImage.status == DogImage.StatusEnum.Valid)

        breed_id = kwargs.get('breed_id')
        if breed_id is not None:
            query = query.filter(DogImage.breed_id == breed_id)

        user_id = kwargs.get('user_id')
        if user_id is not None:
            query = query.filter(DogImage.user_id == user_id)

        query = query.order_by(DogImage.id.desc())
        records = query.paginate(
            page=kwargs['page'], per_page=kwargs['limit'], error_out=False,
        )
        return {
            'items': list(map(DogImageCreate.to_dict, records.items)),
            'page': records.page,
            'limit': records.per_page,
            'total': records.total,
            'pages': records.pages,
            'has_next': records.has_next,
        }


@ns.route('/image/<int:_id>')
@respond_with_code
class DogImageDetail(Resource):
    @classmethod
    @require_login
    def get(cls, _id):
        obj = DogImage.query.filter(
            DogImage.id == _id,
            DogImage.status == DogImage.StatusEnum.Valid,
        ).first()
        if obj is None:
            raise DogImageDoesNotExist(_id)
        return DogImageCreate.to_dict(obj)


@ns.route('/image/<int:_id>')
@respond_with_code
class DogImageDelete(Resource):
    @classmethod
    @require_login
    def delete(cls, _id):
        obj = DogImage.query.filter(
            DogImage.id == _id,
            DogImage.status == DogImage.StatusEnum.Valid,
        ).first()

        if obj is None:
            raise DogImageDoesNotExist(_id)

        if obj.user_id != g.user.id:
            raise DogImageDoesNotExist(_id)

        obj.status = DogImage.StatusEnum.Deleted
        db.session.commit()
        return DogImageCreate.to_dict(obj)
