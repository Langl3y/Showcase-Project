from enum import Enum

from .base import db, ModelBase


class Species(ModelBase):
    class StatusEnum(Enum):
        Valid = 'Valid'
        Deleted = 'Deleted'

    name = db.Column(db.String(128), nullable=False, default='')
    common_name = db.Column(db.String(128), nullable=False, default='')

    status = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.Valid, index=True)

    breeds = db.relationship('Breed', backref='species', lazy='dynamic')


class BreedImage(ModelBase):
    class StatusEnum(Enum):
        Valid = 'Valid'
        Deleted = 'Deleted'

    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=True)
    external_url = db.Column(db.String(1024), nullable=False, default='')

    status = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.Valid, index=True)

    file = db.relationship('File', foreign_keys=[file_id])
    breed = db.relationship('Breed', backref=db.backref('image_obj', uselist=False),
                            foreign_keys='Breed.image_id', uselist=False)

    @property
    def static_url(self) -> str:
        if self.file:
            return self.file.static_url
        return self.external_url or ''

    @property
    def width(self):
        return self.file.width if self.file else None

    @property
    def height(self):
        return self.file.height if self.file else None


class Breed(ModelBase):
    class StatusEnum(Enum):
        Valid = 'Valid'
        Deleted = 'Deleted'

    __table_args__ = (
        db.Index('breed_species_group_idx', 'species_id', 'breed_group'),
        db.Index('breed_country_name_idx', 'country_code', 'name'),
    )

    name = db.Column(db.String(256), nullable=False, default='', index=True)
    species_id = db.Column(db.Integer, db.ForeignKey('species.id'), nullable=False, index=True)

    life_span = db.Column(db.String(32), nullable=True, default=None)
    temperament = db.Column(db.Text, nullable=False, default='')

    origin = db.Column(db.String(128), nullable=True, default=None)
    country_codes = db.Column(db.String(32), nullable=True, default=None)
    country_code = db.Column(db.String(8), nullable=True, default=None, index=True)

    description = db.Column(db.Text, nullable=False, default='')
    bred_for = db.Column(db.String(512), nullable=True, default=None)
    perfect_for = db.Column(db.String(512), nullable=True, default=None)
    breed_group = db.Column(db.String(64), nullable=True, default=None, index=True)
    history = db.Column(db.Text, nullable=False, default='')

    reference_image_id = db.Column(db.String(64), nullable=True, default=None)
    image_id = db.Column(db.Integer, db.ForeignKey('breed_image.id'), nullable=True)

    weight_imperial = db.Column(db.String(32), nullable=True, default=None)
    weight_metric = db.Column(db.String(32), nullable=True, default=None)
    height_imperial = db.Column(db.String(32), nullable=True, default=None)
    height_metric = db.Column(db.String(32), nullable=True, default=None)

    status = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.Valid, index=True)

    def _row_to_dict_hook_(self, result: dict):
        result['weight'] = {
            'imperial': self.weight_imperial,
            'metric': self.weight_metric,
        }
        result['height'] = {
            'imperial': self.height_imperial,
            'metric': self.height_metric,
        }
        img = self.image_obj
        if img:
            f = img.file
            result['image'] = {
                'id': self.reference_image_id,
                'url': img.static_url,
                'width': f.width if f else None,
                'height': f.height if f else None,
                'file_id': f.id if f else None,
            }
        elif self.reference_image_id:
            result['image'] = {
                'id': self.reference_image_id,
                'url': '',
                'width': None,
                'height': None,
                'file_id': None,
            }
        else:
            result['image'] = None

        species = self.species
        result['species_id'] = str(species.id) if species else result.get('species_id')

    @classmethod
    def from_api_payload(cls, payload: dict, auto_commit: bool = False) -> 'Breed':
        from .system import File

        species_id_raw = payload.get('species_id')
        species_id = int(species_id_raw) if species_id_raw is not None else None
        if species_id is not None:
            species = Species.query.get(species_id)
        else:
            species = None
        if not species:
            species = Species(
                name=payload.get('origin') or '',
                common_name=payload.get('origin') or '',
            )
            if species_id is not None:
                species.id = species_id
            db.session.add(species)
            db.session.flush()
            if species_id is None:
                species_id = species.id

        image_payload = payload.get('image') or {}
        image_ref = image_payload.get('id') or payload.get('reference_image_id')
        image_obj = None
        if image_ref:
            key = f"breed_images/{image_ref}.jpg"
            file_obj = File.query.filter(File.key == key).first()
            image_obj = BreedImage.query.filter(BreedImage.file_id == File.id, File.key == key).join(File).first() if file_obj else None
            if not image_obj:
                external_url = image_payload.get('url') or ''
                width = image_payload.get('width')
                height = image_payload.get('height')
                name = f"{image_ref}.jpg"

                if not file_obj:
                    file_obj = File(
                        key=key,
                        name=name,
                        size=0,
                        extra=external_url,
                        mime_type=File.MimeTypeEnum.ImageJpg.value,
                        width=width,
                        height=height,
                    )
                    db.session.add(file_obj)
                    db.session.flush()

                image_obj = BreedImage(
                    file_id=file_obj.id,
                    external_url=external_url,
                )
                db.session.add(image_obj)
                db.session.flush()

        breed_id_raw = payload.get('id')
        breed_id = int(breed_id_raw) if breed_id_raw is not None else None
        breed = Breed.query.get(breed_id) if breed_id is not None else None
        if not breed:
            breed = Breed()
            if breed_id is not None:
                breed.id = breed_id

        breed.name = payload.get('name', breed.name or '')
        breed.species_id = species_id
        breed.life_span = payload.get('life_span')
        breed.temperament = payload.get('temperament') or ''
        breed.origin = payload.get('origin')
        breed.country_codes = payload.get('country_codes')
        breed.country_code = payload.get('country_code')
        breed.description = payload.get('description') or ''
        breed.bred_for = payload.get('bred_for')
        breed.perfect_for = payload.get('perfect_for')
        breed.breed_group = payload.get('breed_group')
        breed.history = payload.get('history') or ''
        breed.reference_image_id = payload.get('reference_image_id') or image_ref
        breed.image_id = image_obj.id if image_obj else None

        weight = payload.get('weight') or {}
        breed.weight_imperial = weight.get('imperial')
        breed.weight_metric = weight.get('metric')

        height = payload.get('height') or {}
        breed.height_imperial = height.get('imperial')
        breed.height_metric = height.get('metric')

        if auto_commit:
            return db.session_add_and_commit(breed)
        db.session.add(breed)
        db.session.flush()
        return breed
