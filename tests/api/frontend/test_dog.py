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


# --- DogImage (user gallery): fixtures + tests ------------------------------

DOG_IMAGE_CREATE_URL = '/frontend/dog/image'
DOG_IMAGES_LIST_URL = '/frontend/dog/images'


def _make_file(app, user_id, *, mime=None, key='tests/dog.jpg', name='dog.jpg',
               size=1024):
    """Persist a File row and return it (no MinIO I/O in tests)."""
    from app.models import File, db

    f = File.new(
        user_id=user_id,
        key=key,
        name=name,
        size=size,
        mime_type=mime or File.MimeTypeEnum.ImageJpg,
    )
    return db.session_add_and_commit(f)


@pytest.fixture
def user2(app):
    """A second persisted user so we can exercise ownership checks."""
    from app.models import User, db

    email, password = 'tester2@example.com', 'Tester123!'
    obj = User.query.filter(User.email == email).first()
    if obj is None:
        obj = User(username='tester2', email=email)
        obj.password = password
        db.session_add_and_commit(obj)
    return email, password


@pytest.fixture
def token2(client, user2):
    email, password = user2
    resp = client.post('/frontend/user/login',
                       json={'email': email, 'password': password})
    return resp.json['data']['token']


@pytest.fixture
def auth2(token2):
    return {'AUTHORIZATION': token2}


@pytest.fixture
def dog_image_file(app, user):
    email, _ = user
    from app.models import User

    u = User.query.filter(User.email == email).first()
    return _make_file(app, u.id)


@pytest.fixture
def dog_image(app, auth, client, breeds, dog_image_file):
    """A single DogImage created via the API; returns (dog_image dict, headers)."""
    payload = {
        'file_id': dog_image_file.id,
        'breed_id': 1,
        'title': 'My Affenpinscher',
    }
    resp = client.post(DOG_IMAGE_CREATE_URL, json=payload, headers=auth)
    assert resp.json['code'] == 0, resp.json
    return resp.json['data'], auth


# ---------- POST /frontend/dog/image ----------

def test_create_dog_image_requires_auth(client, dog_image_file):
    resp = client.post(DOG_IMAGE_CREATE_URL, json={
        'file_id': dog_image_file.id, 'breed_id': 1,
    })
    assert resp.json['code'] != 0


def test_create_dog_image_happy_path(dog_image):
    data, _auth = dog_image
    assert data['id'] > 0
    assert data['breed_id'] == 1
    assert data['file_id'] > 0
    assert data['user_id'] > 0
    assert data['title'] == 'My Affenpinscher'
    assert data['status'] == 'Valid'
    assert data['url'].endswith('tests/dog.jpg') or 'tests/dog.jpg' in data['url']
    assert data['width'] is None
    assert data['height'] is None
    assert data['create_time'] > 0


def test_create_dog_image_missing_file_id_raises(client, auth, breeds):
    resp = client.post(DOG_IMAGE_CREATE_URL,
                       json={'breed_id': 1}, headers=auth)
    assert resp.json['code'] != 0


def test_create_dog_image_nonexistent_file(client, auth, breeds):
    from app.exceptions import FileDoesNotExist

    resp = client.post(DOG_IMAGE_CREATE_URL,
                       json={'file_id': 99999999, 'breed_id': 1}, headers=auth)
    assert resp.json['code'] == FileDoesNotExist.response_code


def test_create_dog_image_nonexistent_breed(client, auth, dog_image_file):
    from app.exceptions import BreedDoesNotExist

    resp = client.post(DOG_IMAGE_CREATE_URL,
                       json={'file_id': dog_image_file.id, 'breed_id': 99999999},
                       headers=auth)
    assert resp.json['code'] == BreedDoesNotExist.response_code


def test_create_dog_image_rejects_non_image_mime(client, auth, app, user):
    """A File uploaded with non-image mime should be rejected."""
    from app.models import User

    email, _ = user
    u = User.query.filter(User.email == email).first()
    pdf = _make_file(app, u.id,
                      mime='DocumentPdf',
                      key='tests/x.pdf', name='x.pdf')
    resp = client.post(DOG_IMAGE_CREATE_URL,
                       json={'file_id': pdf.id, 'breed_id': 1}, headers=auth)
    from app.exceptions import ImageFormatError
    assert resp.json['code'] == ImageFormatError.response_code


def test_create_dog_image_idempotent(client, auth, breeds, dog_image_file, dog_image):
    """POSTing the same (user, breed, file, status=Valid) tuple returns same row."""
    first, _ = dog_image
    payload = {'file_id': dog_image_file.id, 'breed_id': 1}
    second = client.post(DOG_IMAGE_CREATE_URL, json=payload,
                         headers=auth).json['data']
    assert first['id'] == second['id']


def test_create_dog_image_title_is_optional(client, auth, app, user, breeds):
    from app.models import User

    email, _ = user
    u = User.query.filter(User.email == email).first()
    f = _make_file(app, u.id, key='tests/2.jpg', name='2.jpg')
    resp = client.post(DOG_IMAGE_CREATE_URL,
                       json={'file_id': f.id, 'breed_id': 2}, headers=auth)
    assert resp.json['code'] == 0
    assert resp.json['data']['title'] == ''


# ---------- GET /frontend/dog/images & GET /frontend/dog/image/<id> ----------

def test_list_dog_images_requires_auth(client):
    assert client.get(DOG_IMAGES_LIST_URL).json['code'] != 0


def test_list_dog_images_paginates(client, auth, dog_image):
    resp = client.get(DOG_IMAGES_LIST_URL, query_string={'page': 1, 'limit': 1},
                      headers=auth)
    assert resp.json['code'] == 0
    data = resp.json['data']
    assert data['limit'] == 1
    assert data['page'] == 1
    assert data['total'] >= 1
    assert len(data['items']) == 1
    item = data['items'][0]
    assert 'id' in item and 'breed_id' in item and 'url' in item and 'title' in item


def test_list_dog_images_filters_by_breed(client, auth, app, user, breeds):
    """Create two images on different breeds, confirm ?breed_id= isolates them."""
    from app.models import User

    email, _ = user
    u = User.query.filter(User.email == email).first()
    f1 = _make_file(app, u.id, key='tests/b1.jpg', name='b1.jpg')
    f2 = _make_file(app, u.id, key='tests/b2.jpg', name='b2.jpg')
    client.post(DOG_IMAGE_CREATE_URL,
                json={'file_id': f1.id, 'breed_id': 1}, headers=auth)
    client.post(DOG_IMAGE_CREATE_URL,
                json={'file_id': f2.id, 'breed_id': 2}, headers=auth)

    b1 = client.get(DOG_IMAGES_LIST_URL, query_string={'breed_id': 1},
                    headers=auth).json['data']
    b2 = client.get(DOG_IMAGES_LIST_URL, query_string={'breed_id': 2},
                    headers=auth).json['data']
    assert all(i['breed_id'] == 1 for i in b1['items'])
    assert all(i['breed_id'] == 2 for i in b2['items'])
    assert b1['total'] >= 1 and b2['total'] >= 1


def test_list_dog_images_filters_by_user(client, auth, auth2, app, user, breeds):
    from app.models import User

    email, _ = user
    u = User.query.filter(User.email == email).first()
    f1 = _make_file(app, u.id, key='tests/u1.jpg', name='u1.jpg')
    resp1 = client.post(DOG_IMAGE_CREATE_URL,
                        json={'file_id': f1.id, 'breed_id': 1},
                        headers=auth).json['data']

    # user2 has no dog images; file can be owned by any user per current rules
    resp2 = client.post(DOG_IMAGE_CREATE_URL,
                        json={'file_id': f1.id, 'breed_id': 1},
                        headers=auth2).json['data']

    user1_only = client.get(DOG_IMAGES_LIST_URL,
                            query_string={'user_id': resp1['user_id']},
                            headers=auth).json['data']
    user2_only = client.get(DOG_IMAGES_LIST_URL,
                            query_string={'user_id': resp2['user_id']},
                            headers=auth).json['data']
    assert all(i['user_id'] == resp1['user_id'] for i in user1_only['items'])
    assert all(i['user_id'] == resp2['user_id'] for i in user2_only['items'])


def test_detail_dog_image_requires_auth(client, dog_image):
    data, _ = dog_image
    assert client.get(f'{DOG_IMAGE_CREATE_URL}/{data["id"]}').json['code'] != 0


def test_detail_dog_image_happy_path(client, auth, dog_image):
    data, _ = dog_image
    resp = client.get(f'{DOG_IMAGE_CREATE_URL}/{data["id"]}', headers=auth)
    assert resp.json['code'] == 0
    got = resp.json['data']
    assert got['id'] == data['id']
    assert got['breed_id'] == 1
    assert got['title'] == 'My Affenpinscher'
    assert got['status'] == 'Valid'


def test_detail_dog_image_missing_raises(client, auth):
    from app.exceptions import DogImageDoesNotExist

    resp = client.get(f'{DOG_IMAGE_CREATE_URL}/99999999', headers=auth)
    assert resp.json['code'] == DogImageDoesNotExist.response_code


# ---------- DELETE /frontend/dog/image/<id> ----------

def test_delete_dog_image_requires_auth(client, dog_image):
    data, _ = dog_image
    resp = client.delete(f'{DOG_IMAGE_CREATE_URL}/{data["id"]}')
    assert resp.json['code'] != 0


def test_delete_dog_image_owner_soft_deletes(client, auth, dog_image):
    data, _ = dog_image
    resp = client.delete(f'{DOG_IMAGE_CREATE_URL}/{data["id"]}', headers=auth)
    assert resp.json['code'] == 0
    assert resp.json['data']['status'] == 'Deleted'

    # After soft-delete, detail returns DoesNotExist
    from app.exceptions import DogImageDoesNotExist
    detail = client.get(f'{DOG_IMAGE_CREATE_URL}/{data["id"]}', headers=auth)
    assert detail.json['code'] == DogImageDoesNotExist.response_code

    # List also hides deleted
    listed = client.get(DOG_IMAGES_LIST_URL,
                        query_string={'user_id': data['user_id']},
                        headers=auth).json['data']
    ids = [i['id'] for i in listed['items']]
    assert data['id'] not in ids


def test_delete_dog_image_non_owner_raises(client, auth2, dog_image):
    from app.exceptions import DogImageDoesNotExist

    data, _ = dog_image
    resp = client.delete(f'{DOG_IMAGE_CREATE_URL}/{data["id"]}', headers=auth2)
    assert resp.json['code'] == DogImageDoesNotExist.response_code


def test_delete_dog_image_missing_raises(client, auth):
    from app.exceptions import DogImageDoesNotExist

    resp = client.delete(f'{DOG_IMAGE_CREATE_URL}/99999999', headers=auth)
    assert resp.json['code'] == DogImageDoesNotExist.response_code

