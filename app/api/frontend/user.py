from flask import g
from webargs import fields

from app.models import db, User
from app.api.common import (Namespace, respond_with_code, Resource, require_login,
                           get_request_ip, get_request_user_agent, get_request_platform,
                           get_request_language, extra_fields, ex_fields)
from app.exceptions import (InvalidArgument, InvalidUsernameOrPassword,
                           UnAuthorization, EmailAlreadyExists, UserDoesNotExist)
from app.utils.date_ import current_timestamp
from app.utils.rand import new_hex_token
from app.common import LOGIN_TOKEN_SIZE, LOGIN_STATE_DEFAULT_TTL
from app.caches import AuthCache
from app.utils.text import hide_text_default

ns = Namespace('User')


def _user_to_dict(user: User, **kwargs) -> dict:
    return {
        "user_id": user.id,
        "username": hide_text_default(user.username) if user.username else None,
        "email": hide_text_default(user.email) if user.email else None,
        "mobile": hide_text_default(user.mobile) if user.mobile else None,
        "status": user.status.value,
        "login_password_level": user.login_password_level.value,
        "create_time": user.create_time,
        "update_time": user.update_time,
        **kwargs,
    }


@ns.route('/me')
@respond_with_code
class MeResource(Resource):
    @classmethod
    @require_login
    def get(cls):
        user: User = g.user
        return _user_to_dict(user)


@ns.route('/register')
@respond_with_code
class RegisterResource(Resource):

    @classmethod
    @ns.use_kwargs({
        'email': fields.Str(required=True, metadata={'example': 'user@example.com', 'desc': 'User email'}),
        'password': fields.Str(required=True, metadata={'example': 'StrongPass123!', 'desc': 'User password'}),
        'username': fields.Str(required=False, metadata={'example': 'john_doe', 'desc': 'Username'}),
    })
    def post(cls, email: str, password: str, username: str = None):
        if User.query.filter(User.email == email).first():
            raise EmailAlreadyExists(email)

        user = User(
            email=email,
            username=username or email.split('@')[0],
        )
        user.password = password
        db.session_add_and_commit(user)

        return {
            "user_id": user.id,
            "email": user.email,
        }


@ns.route('/login')
@respond_with_code
class LoginResource(Resource):

    @classmethod
    @ns.use_kwargs({
        'email': fields.Str(required=True, metadata={'example': 'user@example.com', 'desc': 'User email'}),
        'password': fields.Str(required=True, metadata={'example': 'StrongPass123!', 'desc': 'User password'}),
    })
    def post(cls, email: str, password: str):
        user = User.query.filter(User.email == email).first()
        if not user:
            raise UserDoesNotExist(email)

        if not user.check_login_password(password):
            raise InvalidUsernameOrPassword()

        if user.status != User.StatusEnum.Valid:
            raise UnAuthorization('Account is not active')

        token = new_hex_token(LOGIN_TOKEN_SIZE)
        ttl = LOGIN_STATE_DEFAULT_TTL
        AuthCache(token).set_user_id(user.id, ttl=ttl)

        return {
            "token": token,
            "user": _user_to_dict(user),
            "expire_time": int(current_timestamp()) + ttl,
        }


@ns.route('/logout')
@respond_with_code
class LogoutResource(Resource):
    @classmethod
    @require_login
    def post(cls):
        from flask import g
        token = getattr(g, 'auth_token', None)
        if token:
            AuthCache(token).delete()
        return {}
