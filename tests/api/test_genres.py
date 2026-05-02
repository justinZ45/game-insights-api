def test_get_all_genres(client):
    response = client.get("/genres/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_genre_by_id(client):
    response = client.get("/genres/1")
    assert response.status_code == 200
    assert response.json()["genre_id"] == 1


def test_get_genre_not_found(client):
    response = client.get("/genres/99999")
    assert response.status_code == 404
