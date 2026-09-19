import requests
from werkzeug.security import generate_password_hash

from app.config import config
from app.models import db, User, Breed


def init_data():
    init_users()
    init_breeds()


def init_users():
    users = [
        {
            'username': 'admin',
            'email': 'admin@example.com',
            'password': 'Admin123!',
        },
        {
            'username': 'user1',
            'email': 'user1@example.com',
            'password': 'User123!',
        },
        {
            'username': 'user2',
            'email': 'user2@example.com',
            'password': 'User123!',
        },
    ]

    for item in users:
        if User.query.filter(User.email == item['email']).first():
            continue
        obj = User(
            username=item['username'],
            email=item['email'],
            login_password_hash=generate_password_hash(item['password']),
        )
        db.session.add(obj)
        db.session.commit()


def init_breeds():
    api_cfg = config.get('THE_DOG_API')
    api_domain = api_cfg.get('API_DOMAIN')
    api_domain = api_domain.rstrip('/')
    endpoint = f'{api_domain}/breeds'

    api_key = api_cfg.get('API_KEY')
    timeout = api_cfg.get('TIMEOUT')

    headers = {}
    if api_key:
        headers['x-api-key'] = api_key

    response = requests.get(endpoint, headers=headers, timeout=timeout)
    response.raise_for_status()
    payloads = response.json()

    for item in payloads:
        raw_id = item.get('id')
        if raw_id is None:
            continue

        breed_id = int(raw_id)
        if Breed.query.get(breed_id) is not None:
            continue

        _ = Breed.from_api_payload(item, auto_commit=True)
