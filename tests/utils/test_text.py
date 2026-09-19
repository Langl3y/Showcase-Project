from datetime import datetime, timezone

import pytest

from app.utils import (
    camel_to_underscore,
    current_milliseconds,
    current_timestamp,
    datetime_to_str,
    hide_text_default,
    new_hex_token,
    new_verification_code,
    now,
    remove_prefix,
    remove_suffix,
    str_to_datetime,
    timestamp_to_datetime,
    today,
    underscore_to_camel,
)
from app.utils.chicken_ribs import NamedObject, classproperty
from app.utils.iterable import list_enum_names, list_enum_values
from app.utils.rand import new_custom_file_key, new_file_key


@pytest.mark.parametrize('value, expected', [
    ('CamelCase', 'camel_case'),
    ('HTTPResponse', 'http_response'),
    ('already_snake', 'already_snake'),
    ('A', 'a'),
])
def test_camel_to_underscore(value, expected):
    assert camel_to_underscore(value) == expected


@pytest.mark.parametrize('value, expected', [
    ('snake_case_name', 'snakeCaseName'),
    ('single', 'single'),
])
def test_underscore_to_camel(value, expected):
    assert underscore_to_camel(value) == expected


def test_remove_prefix_and_suffix():
    assert remove_prefix('UserResource', 'User') == 'Resource'
    assert remove_prefix('Resource', 'User') == 'Resource'
    assert remove_suffix('UserResource', 'Resource') == 'User'
    assert remove_suffix('User', 'Resource') == 'User'


@pytest.mark.parametrize('value, expected', [
    ('', ''),
    ('abcdef', '******'),           # len == start + end -> fully masked
    ('user@example.com', 'use**********com'),
])
def test_hide_text_default(value, expected):
    assert hide_text_default(value) == expected


def test_hide_text_default_custom_window():
    assert hide_text_default('1234567890', start=2, end=2) == '12******90'


def test_random_helpers():
    assert len(new_hex_token(8)) == 16
    assert new_hex_token() != new_hex_token()
    code = new_verification_code()
    assert len(code) == 6 and code.isdigit()
    assert len(new_verification_code(4)) == 4


def test_new_file_key_is_dated_and_unique():
    key = new_file_key(suffix='png')
    prefix, _, name = key.partition('/')
    assert prefix == today().strftime('%Y-%m-%d')
    assert name.endswith('.png')
    assert len(name.removesuffix('.png')) == 32
    assert new_file_key() != new_file_key()


def test_new_file_key_without_suffix_has_no_dot():
    assert '.' not in new_file_key()


def test_new_custom_file_key_uses_folder():
    key = new_custom_file_key('breed_images', suffix='.jpg')
    assert key.startswith('breed_images/')
    assert key.endswith('.jpg')
    assert new_custom_file_key('x') != new_custom_file_key('x')


def test_enum_helpers():
    from app.models import Breed

    assert list_enum_names(Breed.MeasurementEnum) == ['Metric', 'Imperial']
    assert list_enum_values(Breed.MeasurementEnum) == ['Metric', 'Imperial']


def test_named_object_is_falsy_but_prints_its_name():
    empty = NamedObject('Empty')
    assert not empty
    assert str(empty) == 'Empty'
    assert repr(empty) == 'Empty'


def test_classproperty_reads_from_the_class():
    class Thing:
        @classproperty
        def label(cls):
            return 'thing'

    assert Thing.label == 'thing'


def test_timestamp_helpers_agree():
    assert abs(current_milliseconds() // 1000 - current_timestamp()) <= 1
    assert now().tzinfo is timezone.utc
    midnight = today()
    assert (midnight.hour, midnight.minute, midnight.second) == (0, 0, 0)


def test_datetime_conversions_round_trip():
    dt = timestamp_to_datetime(0)
    assert dt == datetime(1970, 1, 1, tzinfo=timezone.utc)

    parsed = str_to_datetime('2026-09-19 10:30:00')
    assert parsed == datetime(2026, 9, 19, 10, 30, tzinfo=timezone.utc)
    assert datetime_to_str(parsed) == '2026-09-19 10:30:00'


def test_datetime_to_str_assumes_utc_when_naive():
    naive = datetime(2026, 9, 19, 10, 30)
    assert datetime_to_str(naive) == '2026-09-19 10:30:00'
