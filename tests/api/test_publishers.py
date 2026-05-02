def test_get_all_publishers(client):
    response = client.get("/publishers/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_publisher_by_id(client):
    response = client.get("/publishers/1")
    assert response.status_code == 200
    assert response.json()["publisher_id"] == 1


def test_get_publisher_not_found(client):
    response = client.get("/publishers/99999")
    assert response.status_code == 404
