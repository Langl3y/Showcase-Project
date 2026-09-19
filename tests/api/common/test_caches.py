from app.caches import AuthCache, UserCache
from app.caches.base import BaseCache


def test_base_cache_round_trip():
    cache = BaseCache('unit:key')
    assert cache.get() is None
    assert cache.exists() is False

    assert cache.set('value') == 'value'
    assert cache.get() == 'value'
    assert cache.exists() is True

    cache.delete()
    assert cache.exists() is False
    cache.delete()  # deleting twice is a no-op


def test_user_cache_namespaces_by_id():
    cache = UserCache(42)
    assert cache.key == 'user:42'
    cache.set_user({'id': 42}, ttl=10)
    assert cache.get_user() == {'id': 42}
    assert UserCache(43).get_user() is None
    cache.delete()


def test_auth_cache_namespaces_by_token():
    cache = AuthCache('tok')
    assert cache.key == 'auth:token:tok'
    cache.set_user_id(7)
    assert cache.get_user_id() == 7
    cache.delete()
    assert AuthCache('tok').get_user_id() is None
