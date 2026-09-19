from unittest.mock import MagicMock, patch

import pytest

BREED_PAYLOAD = [
    {
        'id': 9001,
        'name': 'Test Hound',
        'species_id': 2,
        'life_span': '10-12',
        'temperament': 'Calm',
        'origin': 'Nowhere',
        'country_code': 'NW',
        'country_codes': 'NW',
        'description': 'A breed that exists only in tests.',
        'breed_group': 'Hound',
        'history': 'Invented for a unit test.',
        'reference_image_id': 'ref9001',
        'weight': {'imperial': '20-30', 'metric': '9-14'},
        'height': {'imperial': '10-12', 'metric': '25-30'},
        'image': {'id': 'ref9001', 'url': 'https://example.com/ref9001.jpg',
                  'width': 100, 'height': 50},
    },
    {'id': 9002, 'name': 'No Image Hound', 'species_id': 2,
     'weight': {}, 'height': {}},
    {'name': 'Breed With No Id'},  # skipped: no id to key on
]


@pytest.fixture
def stub_api():
    with patch('app.business.init_data.requests.get') as get:
        get.return_value = MagicMock(json=MagicMock(return_value=BREED_PAYLOAD))
        yield get


def test_init_users_creates_the_demo_accounts(app):
    from app.business import init_users
    from app.models import User

    init_users()
    emails = {'admin@example.com', 'user1@example.com', 'user2@example.com'}
    assert emails <= {u.email for u in User.query.all()}


def test_init_users_is_idempotent(app):
    from app.business import init_users
    from app.models import User

    init_users()
    before = User.query.count()
    init_users()
    assert User.query.count() == before


def test_init_breeds_imports_every_payload_with_an_id(app, stub_api):
    from app.business import init_breeds
    from app.models import Breed

    init_breeds()

    breed = Breed.query.get(9001)
    assert breed.name == 'Test Hound'
    assert breed.weight_metric == '9-14'
    assert breed.height_imperial == '10-12'
    assert breed.reference_image_id == 'ref9001'
    assert Breed.query.get(9002) is not None
    assert Breed.query.filter(Breed.name == 'Breed With No Id').first() is None


def test_init_breeds_calls_the_configured_endpoint(app, stub_api):
    from app.business import init_breeds
    from app.config import config

    init_breeds()

    url = stub_api.call_args.args[0]
    assert url == f"{config['THE_DOG_API']['API_DOMAIN'].rstrip('/')}/breeds"
    assert stub_api.call_args.kwargs['timeout'] == config['THE_DOG_API']['TIMEOUT']


def test_init_breeds_skips_breeds_already_imported(app, stub_api):
    from app.business import init_breeds
    from app.models import Breed

    init_breeds()
    Breed.query.get(9001).name = 'Renamed By Hand'
    init_breeds()

    assert Breed.query.get(9001).name == 'Renamed By Hand'
    assert stub_api.call_count == 2


def test_init_data_runs_both_steps(app, stub_api):
    from app.business import init_data
    from app.models import Breed, User

    init_data()

    assert User.query.filter(User.email == 'admin@example.com').first()
    assert Breed.query.get(9001)


def test_user_business_lookups(app):
    from app.business import UserBusiness
    from app.models import User, db

    user = User(username='biz', email='biz@example.com', mobile='0900000001')
    user.password = 'BizPass123!'
    db.session_add_and_commit(user)

    assert UserBusiness(user.id).get_user().email == 'biz@example.com'
    assert UserBusiness.from_email('biz@example.com').id == user.id
    assert UserBusiness.from_mobile('0900000001').id == user.id
    assert UserBusiness.from_email('nobody@example.com') is None
