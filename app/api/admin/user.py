from webargs import fields

from app.api.common import Namespace, Resource, ex_fields, respond_with_code
from app.exceptions import UserDoesNotExist
from app.models import User, db
from app.utils.text import hide_text_default

ns = Namespace('AdminUser')


@ns.route('/users')
@respond_with_code
class AdminUserListResource(Resource):

    @classmethod
    @ns.use_kwargs({
        'page': ex_fields.PageField,
        'limit': ex_fields.LimitField,
    })
    def get(cls, page: int = 1, limit: int = 20):
        query = User.query.order_by(User.id.desc())
        pagination = query.paginate(page=page, per_page=limit, error_out=False)

        items = [
            {
                "id": u.id,
                "email": hide_text_default(u.email) if u.email else None,
                "mobile": hide_text_default(u.mobile) if u.mobile else None,
                "username": u.username,
                "status": u.status.value,
                "create_time": u.create_time,
            }
            for u in pagination.items
        ]

        return {
            "items": items,
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
        }


@ns.route('/users/<int:user_id>')
@respond_with_code
class AdminUserDetailResource(Resource):
    @classmethod
    def get(cls, user_id: int):
        user = User.query.get(user_id)
        if not user:
            raise UserDoesNotExist(user_id)

        return {
            "id": user.id,
            "email": user.email,
            "mobile": user.mobile,
            "username": user.username,
            "status": user.status.value,
            "login_password_level": user.login_password_level.value,
            "login_password_update_time": user.login_password_update_time,
            "create_time": user.create_time,
            "create_by": user.create_by,
            "update_time": user.update_time,
            "update_by": user.update_by,
        }

    @classmethod
    @ns.use_kwargs({
        'status': fields.Str(required=True, metadata={'example': 'Frozen', 'desc': 'User status: Valid/Frozen/Deleted'}),
    })
    def put(cls, user_id: int, status: str):
        user = User.query.get(user_id)
        if not user:
            raise UserDoesNotExist(user_id)

        try:
            user.status = User.StatusEnum(status)
        except ValueError as exc:
            from app.exceptions import InvalidArgument
            raise InvalidArgument(f'Invalid status: {status}') from exc

        db.session.commit()

        return {
            "user_id": user.id,
            "status": user.status.value,
        }
