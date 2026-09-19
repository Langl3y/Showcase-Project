def test_health(client):
    resp = client.get('/frontend/system/health')

    assert resp.status_code == 200
    assert resp.json['code'] == 0
    assert resp.json['data']['status'] == 'healthy'


def test_info(client):
    resp = client.get('/frontend/system/info')

    assert resp.status_code == 200
    assert resp.json['data']['api_prefixes'] == ['/frontend', '/admin']
