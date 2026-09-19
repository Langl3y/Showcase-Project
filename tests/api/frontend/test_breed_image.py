import pytest

ATTACH_URL = '/frontend/dog/breed/image'
BREED_DETAIL_URL = '/frontend/dog/breed'


@pytest.fixture
def auth(token):
    return {'AUTHORIZATION': token}


@pytest.fixture
def breed(app):
    from app.models import Breed, Species, db

    species = Species.get_or_create(name='Attach', common_name='Attach',
                                    auto_commit=True)
    obj = Breed(name='Attachable', species_id=species.id,
                reference_image_id='from-the-dog-api')
    return db.session_add_and_commit(obj)


def _file(mime=None, key='attach/a.png'):
    from app.models import File, db

    obj = File.new(None, key, 'a.png', size=12,
                   mime_type=mime or File.MimeTypeEnum.ImagePng,
                   width=8, height=4)
    return db.session_add_and_commit(obj)


def test_requires_a_token(client, breed):
    assert client.post(ATTACH_URL,
                       json={'file_id': 1, 'breed_id': breed.id}).json['code'] != 0


def test_file_id_and_breed_id_are_required(client, auth):
    assert client.post(ATTACH_URL, json={}, headers=auth).json['code'] != 0


def test_attaches_the_file_to_the_breed(client, auth, breed, app):
    from app.models import Breed

    row = _file()
    body = client.post(ATTACH_URL, headers=auth,
                       json={'file_id': row.id, 'breed_id': breed.id}).json

    assert body['code'] == 0
    assert body['data']['breed_id'] == breed.id
    assert body['data']['file_id'] == row.id
    assert body['data']['url'].endswith('attach/a.png')
    assert Breed.query.get(breed.id).image_id == body['data']['image_id']


def test_clears_the_dog_api_reference_id(client, auth, breed, app):
    from app.models import Breed

    row = _file(key='attach/ref.png')
    client.post(ATTACH_URL, headers=auth,
                json={'file_id': row.id, 'breed_id': breed.id})

    assert Breed.query.get(breed.id).reference_image_id is None


def test_the_breed_detail_then_serves_the_new_image(client, auth, breed):
    row = _file(key='attach/detail.png')
    client.post(ATTACH_URL, headers=auth,
                json={'file_id': row.id, 'breed_id': breed.id})

    image = client.get(f'{BREED_DETAIL_URL}/{breed.id}', headers=auth).json['data']['image']
    assert image['url'].endswith('attach/detail.png')
    assert image['file_id'] == row.id


def test_attaching_the_same_file_twice_is_idempotent(client, auth, breed, app):
    from app.models import BreedImage

    row = _file(key='attach/same.png')
    payload = {'file_id': row.id, 'breed_id': breed.id}

    first = client.post(ATTACH_URL, headers=auth, json=payload).json['data']
    count = BreedImage.query.count()
    second = client.post(ATTACH_URL, headers=auth, json=payload).json['data']

    assert first['image_id'] == second['image_id']
    assert BreedImage.query.count() == count


def test_replacing_the_image_retires_the_previous_one(client, auth, breed, app):
    from app.models import BreedImage

    old = _file(key='attach/old.png')
    new = _file(key='attach/new.png')

    first = client.post(ATTACH_URL, headers=auth,
                        json={'file_id': old.id, 'breed_id': breed.id}).json['data']
    second = client.post(ATTACH_URL, headers=auth,
                         json={'file_id': new.id, 'breed_id': breed.id}).json['data']

    assert first['image_id'] != second['image_id']
    assert BreedImage.query.get(first['image_id']).status is \
        BreedImage.StatusEnum.Deleted
    assert BreedImage.query.get(second['image_id']).status is \
        BreedImage.StatusEnum.Valid


def test_rejects_an_unknown_file(client, auth, breed):
    from app.exceptions import FileDoesNotExist

    body = client.post(ATTACH_URL, headers=auth,
                       json={'file_id': 999999, 'breed_id': breed.id}).json
    assert body['code'] == FileDoesNotExist.response_code


def test_rejects_a_file_that_is_not_an_image(client, auth, breed, app):
    from app.exceptions import ImageFormatError
    from app.models import File

    row = _file(mime=File.MimeTypeEnum.DocumentPdf, key='attach/doc.pdf')
    body = client.post(ATTACH_URL, headers=auth,
                       json={'file_id': row.id, 'breed_id': breed.id}).json
    assert body['code'] == ImageFormatError.response_code


def test_rejects_a_deleted_file(client, auth, breed, app):
    from app.exceptions import FileDoesNotExist
    from app.models import File, db

    row = _file(key='attach/gone.png')
    row.status = File.StatusEnum.Invalid
    db.session.commit()

    body = client.post(ATTACH_URL, headers=auth,
                       json={'file_id': row.id, 'breed_id': breed.id}).json
    assert body['code'] == FileDoesNotExist.response_code


def test_rejects_an_unknown_breed(client, auth):
    from app.exceptions import BreedDoesNotExist

    row = _file(key='attach/nobreed.png')
    body = client.post(ATTACH_URL, headers=auth,
                       json={'file_id': row.id, 'breed_id': 999999}).json
    assert body['code'] == BreedDoesNotExist.response_code
