def test_list_users(client, user):
    resp = client.get('/admin/user/users', query_string={'page': 1, 'limit': 10})

    assert resp.json['code'] == 0
    data = resp.json['data']
    assert data['total'] >= 1
    assert len(data['items']) <= 10


def test_get_and_update_user(client, user):
    user_id = client.get('/admin/user/users').json['data']['items'][0]['id']

    resp = client.get(f'/admin/user/users/{user_id}')
    assert resp.json['code'] == 0

    resp = client.put(f'/admin/user/users/{user_id}', json={'status': 'Frozen'})
    assert resp.json['data']['status'] == 'Frozen'

    client.put(f'/admin/user/users/{user_id}', json={'status': 'Valid'})


def test_get_missing_user(client):
    assert client.get('/admin/user/users/999999').json['code'] != 0


def test_update_with_invalid_status(client, user):
    user_id = client.get('/admin/user/users').json['data']['items'][0]['id']

    assert client.put(f'/admin/user/users/{user_id}',
                      json={'status': 'Nope'}).json['code'] != 0
