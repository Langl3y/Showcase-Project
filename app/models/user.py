from enum import Enum
from werkzeug.security import check_password_hash, generate_password_hash

from .base import db, ModelBase
from app.utils.date_ import current_timestamp


class User(ModelBase):
    class StatusEnum(Enum):
        Valid = 'Valid'
        Deleted = 'Deleted'
        Frozen = 'Frozen'

    class PasswordLevelEnum(Enum):
        Low = 'Low'
        Middle = 'Middle'
        High = 'High'

    username = db.Column(db.String(256), nullable=True, default=None)
    email = db.Column(db.String(128), nullable=True, default=None, unique=True)
    mobile = db.Column(db.String(64), nullable=True, default=None, unique=True)

    login_password_hash = db.Column(db.String(512), nullable=False, default='')
    login_password_level = db.Column(db.Enum(PasswordLevelEnum), nullable=False, default=PasswordLevelEnum.Low)
    login_password_update_time = db.Column(db.Integer)

    status = db.Column(db.Enum(StatusEnum), nullable=False, default=StatusEnum.Valid, index=True)

    dog_images = db.relationship(
        'DogImage',
        primaryjoin="and_(DogImage.user_id == User.id, "
                    "DogImage.status == 'Valid')",
        foreign_keys='DogImage.user_id',
        uselist=True,
        lazy='dynamic',
        viewonly=True,
    )

    def check_login_password(self, password: str) -> bool:
        if self.login_password_hash is None:
            return False
        return check_password_hash(self.login_password_hash, password)

    @property
    def password(self):
        return

    @password.setter
    def password(self, password: str):
        self.login_password_hash = generate_password_hash(password)

    def set_login_password(self, password: str):
        self.login_password_hash = generate_password_hash(password)
        self.login_password_update_time = current_timestamp()
        db.session.commit()
