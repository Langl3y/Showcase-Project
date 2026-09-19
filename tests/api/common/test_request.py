import pytest

from app.api.common.request import (
    RequestPlatform,
    get_request_data,
    get_request_info,
    get_request_ip,
    get_request_language,
    get_request_platform,
    get_request_user,
    get_request_user_agent,
)
from app.common import LanguageEnum
from app.exceptions import InvalidPlatform


def test_platform_predicates():
    assert RequestPlatform.WEB.is_web()
    assert RequestPlatform.iOS.is_ios() and RequestPlatform.iOS.is_mobile()
    assert RequestPlatform.ANDROID.is_android() and RequestPlatform.ANDROID.is_mobile()
    assert not RequestPlatform.WEB.is_mobile()
    assert not RequestPlatform.UNKNOWN.is_web()


@pytest.mark.parametrize('header, expected', [
    ('WEB', RequestPlatform.WEB),
    ('iOS', RequestPlatform.iOS),
    ('Android', RequestPlatform.ANDROID),
])
def test_platform_from_header(app, header, expected):
    with app.test_request_context('/', headers={'PLATFORM': header}):
        assert get_request_platform() is expected


def test_platform_defaults_to_unknown_when_absent(app):
    with app.test_request_context('/'):
        assert get_request_platform() is RequestPlatform.UNKNOWN


@pytest.mark.parametrize('header', ['Nonsense', 'UNKNOWN'])
def test_platform_rejects_bad_values(app, header):
    with app.test_request_context('/', headers={'PLATFORM': header}):
        with pytest.raises(InvalidPlatform):
            get_request_platform()


def test_ip_falls_back_to_localhost(app):
    with app.test_request_context('/', environ_base={'REMOTE_ADDR': '10.0.0.7'}):
        assert get_request_ip() == '10.0.0.7'
    with app.test_request_context('/', environ_base={'REMOTE_ADDR': ''}):
        assert get_request_ip() == '127.0.0.1'


def test_language_header(app):
    with app.test_request_context('/', headers={'Accept-Language': 'zh_CN'}):
        assert get_request_language() is LanguageEnum.zh_CN
    with app.test_request_context('/', headers={'Accept-Language': 'klingon'}):
        assert get_request_language() is LanguageEnum.en_US
    with app.test_request_context('/'):
        assert get_request_language() is LanguageEnum.en_US


def test_user_agent(app):
    with app.test_request_context('/', headers={'User-Agent': 'pytest/1.0'}):
        assert get_request_user_agent() == 'pytest/1.0'


def test_request_data_reads_query_then_body(app):
    with app.test_request_context('/?a=1&b=2'):
        assert get_request_data() == {'a': '1', 'b': '2'}
    with app.test_request_context('/', json={'x': 9}):
        assert get_request_data() == {'x': 9}


def test_request_info_summarises_the_call(app):
    with app.test_request_context('/frontend/user/me?q=1',
                                  headers={'PLATFORM': 'WEB'}):
        info = get_request_info()

    assert info['path'] == '/frontend/user/me'
    assert info['method'] == 'GET'
    assert info['platform'] == 'WEB'
    assert info['language'] == 'en_US'
    assert info['data'] == {'q': '1'}
    assert info['request_time'].tzinfo is not None


def test_request_user_is_none_until_login_sets_it(app):
    from flask import g

    with app.test_request_context('/'):
        assert get_request_user() is None
        g.user = 'sentinel'
        assert get_request_user() == 'sentinel'
