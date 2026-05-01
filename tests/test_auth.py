def test_without_api_key_returns_401(client):
    response = client.get("/accounts")
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_invalid_api_key_returns_401(client):
    response = client.get("/accounts", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_valid_api_key_passes_auth_layer(client):
    response = client.get("/accounts", headers={"X-API-Key": "test-key"})
    assert response.status_code == 200
