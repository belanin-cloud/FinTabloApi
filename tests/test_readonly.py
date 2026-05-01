def test_post_transactions_returns_405(client):
    response = client.post("/transactions", headers={"X-API-Key": "test-key"})
    assert response.status_code == 405


def test_put_transactions_returns_405(client):
    response = client.put("/transactions", headers={"X-API-Key": "test-key"})
    assert response.status_code == 405


def test_delete_transactions_returns_405(client):
    response = client.delete("/transactions", headers={"X-API-Key": "test-key"})
    assert response.status_code == 405
