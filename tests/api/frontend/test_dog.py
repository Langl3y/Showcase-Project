import pytest


BREED_PAYLOADS = [
    {
        'id': 1,
        'name': 'Affenpinscher',
        'species_id': 2,
        'life_span': '12-15',
        'temperament': 'Confident, alert, playful',
        'origin': 'Germany',
        'country_code': 'DE',
        'country_codes': 'DE',
        'description': 'Small, sturdy toy breed.',
        'bred_for': 'Small rodent hunting',
        'breed_group': 'Toy',
        'history': 'Originating in 17th-century Germany.',
        'reference_image_id': 'affen01',
        'weight': {'imperial': '7-10', 'metric': '3.2-4.5'},
        'height': {'imperial': '9-11.5', 'metric': '23-29'},
        'image': {'id': 'affen01', 'url': 'https://example.com/affen01.jpg',
                  'width': 640, 'height': 480},
    },
    {
        'id': 2,
        'name': 'Afghan Hound',
        'species_id': 2,
        'life_span': '10-13',
        'temperament': 'Aloof, dignified',
        'origin': 'Afghanistan',
        'country_code': 'AF',
        'country_codes': 'AF',
        'description': 'Tall, elegant sighthound.',
        'breed_group': 'Hound',
        'history': 'Ancient sighthound of the Afghan mountains.',
        'weight': {'imperial': '50-60', 'metric': '23-27'},
        'height': {'imperial': '25-27', 'metric': '64-69'},
    },
    {
        'id': 3,
        'name': 'Akita',
        'species_id': 2,
        'life_span': '10-12',
        'temperament': 'Courageous, loyal',
        'origin': 'Japan',
        'country_code': 'JP',
        'country_codes': 'JP',
        'description': 'Large spitz-type breed.',
        'breed_group': 'Working',
        'history': 'Bred in the mountains of northern Japan.',
        'weight': {'imperial': '70-130', 'metric': '32-59'},
        'height': {'imperial': '24-28', 'metric': '61-71'},
    },
]

LIST_URL = '/frontend/dog/breed'


@pytest.fixture
def breeds(app):
    """Three persisted breeds; returns the source payloads."""
    from app.models import Breed

    for payload in BREED_PAYLOADS:
        Breed.from_api_payload(payload, auto_commit=True)

    return BREED_PAYLOADS


@pytest.fixture
def auth(token):
    return {'AUTHORIZATION': token}


# --- GET /frontend/dog/breed -------------------------------------------------

def test_list_requires_token(client, breeds):
    assert client.get(LIST_URL).json['code'] != 0


def test_list_returns_breeds(client, auth, breeds):
    resp = client.get(LIST_URL, headers=auth)

    assert resp.json['code'] == 0
    data = resp.json['data']
    assert data['total'] >= len(breeds)
    assert data['page'] == 1
    assert data['limit'] == 50
    assert {'id', 'name'} == set(data['items'][0])
    assert data['items'][0]['name'] == 'Affenpinscher'


def test_list_paginates(client, auth, breeds):
    first = client.get(LIST_URL, query_string={'page': 1, 'limit': 1},
                       headers=auth).json['data']
    second = client.get(LIST_URL, query_string={'page': 2, 'limit': 1},
                        headers=auth).json['data']

    assert len(first['items']) == 1
    assert first['limit'] == 1
    assert first['has_next'] is True
    assert first['pages'] == first['total']
    assert first['items'][0]['id'] != second['items'][0]['id']


def test_list_page_past_the_end_is_empty(client, auth, breeds):
    """error_out=False: an out-of-range page is empty, not a 404."""
    resp = client.get(LIST_URL, query_string={'page': 9999}, headers=auth)

    assert resp.json['code'] == 0
    data = resp.json['data']
    assert data['items'] == []
    assert data['has_next'] is False
    assert data['total'] >= len(breeds)


@pytest.mark.parametrize('page', [0, -1])
def test_list_clamps_non_positive_page(client, auth, breeds, page):
    resp = client.get(LIST_URL, query_string={'page': page}, headers=auth)

    assert resp.json['code'] == 0
    assert resp.json['data']['items']


def test_list_rejects_non_integer_page(client, auth, breeds):
    assert client.get(LIST_URL, query_string={'page': 'abc'},
                      headers=auth).json['code'] != 0


# --- GET /frontend/dog/breed/<id> --------------------------------------------

def test_detail_requires_token(client, breeds):
    assert client.get(f'{LIST_URL}/1').json['code'] != 0


def test_detail_returns_breed(client, auth, breeds):
    resp = client.get(f'{LIST_URL}/1', headers=auth)

    assert resp.json['code'] == 0
    data = resp.json['data']
    assert data['id'] == 1
    assert data['name'] == 'Affenpinscher'
    assert data['breed_group'] == 'Toy'
    assert data['origin'] == 'Germany'
    assert data['status'] == 'Valid'
    assert data['image']['id'] == 'affen01'


def test_detail_defaults_to_metric(client, auth, breeds):
    data = client.get(f'{LIST_URL}/1', headers=auth).json['data']

    assert data['measurement'] == 'Metric'
    assert data['weight'] == '3.2-4.5'
    assert data['height'] == '23-29'


def test_detail_honours_imperial(client, auth, breeds):
    data = client.get(f'{LIST_URL}/1', query_string={'measurement': 'Imperial'},
                      headers=auth).json['data']

    assert data['measurement'] == 'Imperial'
    assert data['weight'] == '7-10'
    assert data['height'] == '9-11.5'


def test_detail_blank_measurement_falls_back_to_metric(client, auth, breeds):
    data = client.get(f'{LIST_URL}/1', query_string={'measurement': ''},
                      headers=auth).json['data']

    assert data['measurement'] == 'Metric'
    assert data['weight'] == '3.2-4.5'


def test_detail_rejects_unknown_measurement(client, auth, breeds):
    resp = client.get(f'{LIST_URL}/1', query_string={'measurement': 'Nonsense'},
                      headers=auth)

    assert resp.json['code'] != 0
    assert 'Nonsense' in resp.json['message']


def test_detail_missing_breed(client, auth, breeds):
    from app.exceptions import BreedDoesNotExist

    resp = client.get(f'{LIST_URL}/999999', headers=auth)

    assert resp.json['code'] == BreedDoesNotExist.response_code
    assert resp.json['message'] == 'Breed does not exist'
