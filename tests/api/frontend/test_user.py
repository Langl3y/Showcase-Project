def test_register_and_login(client):
    payload = {'email': 'new@example.com', 'password': 'NewUser123!'}

    resp = client.post('/frontend/user/register', json=payload)
    assert resp.json['code'] == 0
    assert resp.json['data']['email'] == payload['email']

    resp = client.post('/frontend/user/login', json=payload)
    assert resp.json['code'] == 0
    assert resp.json['data']['token']


def test_register_rejects_duplicate_email(client, user):
    email, password = user

    resp = client.post('/frontend/user/register',
                       json={'email': email, 'password': password})

    assert resp.json['code'] != 0


def test_login_rejects_wrong_password(client, user):
    email, _ = user

    resp = client.post('/frontend/user/login',
                       json={'email': email, 'password': 'WrongPass123!'})

    assert resp.json['code'] != 0


def test_me_requires_token(client):
    assert client.get('/frontend/user/me').json['code'] != 0


def test_me_and_logout(client, token):
    resp = client.get('/frontend/user/me', headers={'AUTHORIZATION': token})
    assert resp.json['code'] == 0
    assert resp.json['data']['user_id']

    resp = client.post('/frontend/user/logout', headers={'AUTHORIZATION': token})
    assert resp.json['code'] == 0

    resp = client.get('/frontend/user/me', headers={'AUTHORIZATION': token})
    assert resp.json['code'] != 0
