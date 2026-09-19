from typing import Any, Optional


class BaseCache:
    _backend: dict = {}

    def __init__(self, key: str):
        self.key = key

    def get(self) -> Optional[Any]:
        return self._backend.get(self.key)

    def set(self, value: Any, ttl: Optional[int] = None):
        self._backend[self.key] = value
        return value

    def delete(self):
        if self.key in self._backend:
            del self._backend[self.key]

    def exists(self) -> bool:
        return self.key in self._backend


class UserCache(BaseCache):

    def __init__(self, user_id: int):
        super().__init__(f'user:{user_id}')
        self.user_id = user_id

    def set_user(self, user_data: dict, ttl: int = 3600):
        return self.set(user_data, ttl)

    def get_user(self) -> Optional[dict]:
        return self.get()


class AuthCache(BaseCache):

    def __init__(self, token: str):
        super().__init__(f'auth:token:{token}')
        self.token = token

    def set_user_id(self, user_id: int, ttl: int = 86400):
        return self.set(user_id, ttl)

    def get_user_id(self) -> Optional[int]:
        return self.get()
