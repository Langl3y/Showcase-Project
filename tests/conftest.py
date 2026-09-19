import os
import tempfile

os.environ['TESTING'] = '1'

import pytest


@pytest.fixture(scope='session')
def app():
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)

    # The config dict is read by create_app(), and Flask-SQLAlchemy binds its
    # engine during init_app(), so the override has to happen before that.
    from app.config import config
    config['TESTING'] = True
    config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    from app import create_app
    from app.models import db

    flask_app = create_app()

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    """A persisted user; returns (email, password)."""
    from app.models import db, User

    email, password = 'tester@example.com', 'Tester123!'
    obj = User.query.filter(User.email == email).first()
    if obj is None:
        obj = User(username='tester', email=email)
        obj.password = password
        db.session_add_and_commit(obj)

    return email, password


@pytest.fixture
def token(client, user):
    email, password = user
    resp = client.post('/frontend/user/login',
                       json={'email': email, 'password': password})
    return resp.json['data']['token']
