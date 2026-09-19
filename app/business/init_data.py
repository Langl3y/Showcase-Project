import requests

from werkzeug.security import generate_password_hash
from app.models import db, User


def init_data():
    init_users()


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
    breeds = []

    
