import pytest

from app.models import Breed, BreedImage, DogImage, File, Species, User, db
from app.models.base import get_primary_key, new_session, row_to_dict


@pytest.fixture
def species(app):
    obj = Species.get_or_create(name='Canis', common_name='Dog',
                                auto_commit=True)
    return obj


def _file(key='models/a.png', **kw):
    obj = File.new(None, key, kw.pop('name', 'a.png'),
                   size=kw.pop('size', 10),
                   mime_type=kw.pop('mime_type', File.MimeTypeEnum.ImagePng),
                   width=kw.pop('width', 64), height=kw.pop('height', 32), **kw)
    return db.session_add_and_commit(obj)


def test_get_or_create_returns_the_existing_row(app, species):
    again = Species.get_or_create(name='Canis', common_name='Dog')
    assert again.id == species.id


def test_get_or_create_without_commit_leaves_it_unsaved(app):
    obj = Species.get_or_create(name='Uncommitted', common_name='U')
    assert obj.id is None


def test_get_primary_key():
    assert get_primary_key(Breed) == 'id'


def test_new_session_is_usable_and_closes(app):
    with new_session() as session:
        assert session.query(Species).count() >= 0


def test_row_to_dict_can_skip_the_hook(app, species):
    plain = row_to_dict(species, with_hook=False)
    assert plain['name'] == 'Canis'
    assert plain['status'] is Species.StatusEnum.Valid


def test_row_to_dict_can_render_enums_by_name(app, species):
    assert row_to_dict(species, enum_to_name=True)['status'] == 'Valid'


def test_row_to_dict_swallows_a_failing_hook(app, species):
    def boom(_result):
        raise RuntimeError('hook exploded')

    species._row_to_dict_hook_ = boom
    try:
        assert row_to_dict(species)['name'] == 'Canis'
    finally:
        del species._row_to_dict_hook_


def test_password_is_write_only_and_hashed(app):
    user = User(username='pw', email='pw@example.com')
    user.password = 'Secret123!'

    assert user.password is None
    assert user.login_password_hash != 'Secret123!'
    assert user.check_login_password('Secret123!')
    assert not user.check_login_password('wrong')


def test_check_password_without_a_hash_is_false(app):
    assert User(username='x', email='x@example.com').check_login_password('a') is False


def test_set_login_password_stamps_the_update_time(app):
    user = User(username='stamp', email='stamp@example.com')
    user.password = 'Old12345!'
    db.session_add_and_commit(user)

    user.set_login_password('New12345!')
    assert user.check_login_password('New12345!')
    assert user.login_password_update_time is not None


def test_file_urls_and_payload(app):
    row = _file()
    assert row.static_url.endswith('/models/a.png')
    assert 'models/a.png' in row.private_url

    data = row.all_data
    assert data['file_name'] == 'a.png'
    assert (data['width'], data['height']) == (64, 32)


def test_file_hook_adds_both_urls(app):
    row = _file(key='models/hook.png')
    payload = row.to_dict()
    assert payload['static_url'].endswith('models/hook.png')
    assert payload['private_url']


def test_file_new_rejects_an_unsupported_provider(app):
    with pytest.raises(ValueError, match='Unsupported provider'):
        File.new(None, 'k', 'n', provider='S3')


def test_file_new_accepts_a_plain_mime_string(app):
    row = File.new(None, 'models/plain.bin', 'plain.bin', mime_type='File')
    assert row.mime_type == 'File'


def test_urls_are_empty_for_a_non_minio_provider(app):
    from app.config import config

    row = File(bucket=config['MINIO_FILE']['bucket_name'],
               key='models/other.png', name='other.png')
    row.provider = None

    assert row.static_url == ''
    assert row.private_url == ''


def test_breed_hook_reports_no_image(app, species):
    breed = db.session_add_and_commit(
        Breed(name='Imageless', species_id=species.id))
    assert breed.to_dict()['image'] is None


def test_breed_hook_falls_back_to_the_reference_id(app, species):
    breed = db.session_add_and_commit(
        Breed(name='RefOnly', species_id=species.id, reference_image_id='ref1'))
    image = breed.to_dict()['image']
    assert image == {'id': 'ref1', 'url': '', 'width': None, 'height': None,
                     'file_id': None}


def test_breed_hook_stringifies_the_species_id(app, species):
    breed = db.session_add_and_commit(
        Breed(name='Speciesful', species_id=species.id))
    assert breed.to_dict()['species_id'] == str(species.id)


def test_breed_image_prefers_the_file_over_the_external_url(app):
    row = _file(key='models/breedimg.png')
    image = db.session_add_and_commit(
        BreedImage(file_id=row.id, external_url='https://example.com/x.png'))
    assert image.static_url.endswith('models/breedimg.png')
    assert (image.width, image.height) == (64, 32)


def test_breed_image_uses_the_external_url_without_a_file(app):
    image = db.session_add_and_commit(
        BreedImage(external_url='https://example.com/ext.png'))
    assert image.static_url == 'https://example.com/ext.png'
    assert image.width is None and image.height is None


def test_breed_image_with_nothing_at_all(app):
    assert db.session_add_and_commit(BreedImage()).static_url == ''


def test_dog_image_mirrors_its_file(app, species):
    breed = db.session_add_and_commit(Breed(name='Doggy', species_id=species.id))
    row = _file(key='models/dogimg.png')
    image = db.session_add_and_commit(
        DogImage(breed_id=breed.id, file_id=row.id, user_id=1))

    assert image.static_url.endswith('models/dogimg.png')
    assert (image.width, image.height) == (64, 32)


def test_dog_image_without_a_file_uses_external_url(app, species):
    breed = db.session_add_and_commit(Breed(name='Doggy2', species_id=species.id))
    image = db.session_add_and_commit(
        DogImage(breed_id=breed.id, user_id=1,
                 external_url='https://example.com/d.png'))
    assert image.static_url == 'https://example.com/d.png'
    assert image.width is None and image.height is None
