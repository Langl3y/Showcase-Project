from app.models import User


class UserBusiness:

    def __init__(self, user_id: int):
        self.user_id = user_id

    def get_user(self) -> User:
        return User.query.get(self.user_id)

    @classmethod
    def from_email(cls, email: str):
        return User.query.filter(User.email == email).first()

    @classmethod
    def from_mobile(cls, mobile: str):
        return User.query.filter(User.mobile == mobile).first()
