def test_get_all_games(client):
    response = client.get("/games/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_game_by_id(client):
    response = client.get("/games/1")
    assert response.status_code == 200
    assert response.json()["game_id"] == 1


def test_get_game_not_found(client):
    response = client.get("/games/99999")
    assert response.status_code == 404


def test_filter_by_console(client, sample_game):
    response = client.get("/games/?console=Nintendo DS")
    assert response.status_code == 200
    results = response.json()
    assert all(g["console"] == "Nintendo DS" for g in results)


def test_filter_by_genre(client):
    response = client.get("/games/?genre=Action")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_filter_by_min_review_score(client):
    response = client.get("/games/?min_review_score=80")
    assert response.status_code == 200
    results = response.json()
    assert all(g["review_score"] >= 80 for g in results)


def test_limit_and_offset(client):
    response = client.get("/games/?limit=5&offset=0")
    assert response.status_code == 200
    assert len(response.json()) <= 5


def test_invalid_limit(client):
    response = client.get("/games/?limit=abc")
    assert response.status_code == 422  # FastAPI validation error
