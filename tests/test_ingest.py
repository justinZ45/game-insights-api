import pytest
import httpx
from pydantic import ValidationError
from src.models.pydantic_models import GameInput
from src.db.ingest import clean_data, seed_from_url
from unittest.mock import MagicMock, patch


def test_clean_data(sample_game):
    """Verify that clean_data returns the list of processed games."""
    # Only expect ONE return value (the games list)
    games = clean_data([sample_game], {}, {})
    assert games[0].title == "Super Mario"


def test_clean_data_genre_cache(sample_game):
    """Same genre across two games should produce one cache entry."""
    genre_cache = {}
    # Python modifies genre_cache in place! No need to unpack it.
    clean_data([sample_game, sample_game], genre_cache, {})
    assert len(genre_cache) == 1


def test_clean_data_publisher_cache(sample_game):
    """Same publisher across two games should produce one cache entry."""
    publisher_cache = {}
    # Python modifies publisher_cache in place! No need to unpack it.
    clean_data([sample_game, sample_game], {}, publisher_cache)
    assert len(publisher_cache) == 1


def test_clean_data_invalid_game_skipped():
    """clean_data should skip games that fail Pydantic validation."""
    bad_game = {"Title": "Bad Game"}
    # Only expect ONE return value (the games list)
    games = clean_data([bad_game], {}, {})
    assert len(games) == 0


@pytest.mark.parametrize("year", [1910, 2050])
def test_invalid_year(sample_game, year):
    """GameJsonInput should reject years less than 1950 and above the current year"""
    sample_game["Release"]["Year"] = year

    with pytest.raises(ValidationError):
        GameInput.model_validate(sample_game)


@pytest.mark.parametrize("price", [56.95819, 20.999])
def test_price_two_decimal(sample_game, price):
    """GameJsonInput should reject used prices that are not to 2 decimal places"""
    sample_game["Metrics"]["Used Price"] = price

    with pytest.raises(ValidationError):
        GameInput.model_validate(sample_game)


@pytest.mark.parametrize(
    "esrb_rating, expected",
    [
        ("PG", "RP"),
        ("18+", "RP"),
        ("invalid", "RP"),
        ("e", "E"),  # lowercase gets uppercased
        ("m", "M"),  # lowercase gets uppercased
        (None, "RP"),  # None defaults to RP
    ],
)
def test_esrb_rating_normalization(sample_game, esrb_rating, expected):
    """ESRB validator should normalize valid ratings and default invalid ones to RP."""
    sample_game["Release"]["Rating"] = esrb_rating
    game = GameInput.model_validate(sample_game, by_alias=True)
    assert game.release.esrb_rating == expected


@pytest.mark.parametrize(
    "field, value",
    [
        (["Length", "Main Story", "Average"], -89.23),
        (["Length", "Main Story", "Leisure"], -5.8902384),
        (["Length", "Main Story", "Median"], -2),
        (["Length", "Main Story", "Polled"], -200),  # lowercase gets uppercased
        (["Length", "Main Story", "Rushed"], -56.19),  # lowercase gets uppercased
        (["Metrics", "Review Score"], -5),
        (["Metrics", "Review Score"], 106),
        (["Metrics", "Sales"], -35.60),
        (["Metrics", "Used Price"], -59.99),
    ],
)
def test_greater_than_eq_zero(sample_game, field, value):
    """GameJsonInput should reject fields with validation error when less than 0."""
    if len(field) == 3:
        sample_game[field[0]][field[1]][field[2]] = value
    else:
        sample_game[field[0]][field[1]] = value

    with pytest.raises(ValidationError):
        GameInput.model_validate(sample_game)



@patch("src.db.ingest.httpx.get")
@patch("src.db.ingest._process_and_insert")
def test_seed_from_url_success(mock_process, mock_get):
    """seed_from_url should fetch JSON and call processing pipeline on success."""
    # Mocking successful httpx response
    mock_response = MagicMock()
    mock_response.json.return_value = [{"Title": "Mock Game"}]
    mock_response.raise_for_status = MagicMock() # does nothing, mimicking success
    mock_get.return_value = mock_response

    mock_db = MagicMock()
    
    seed_from_url(mock_db, "https://fakeurl.com/games.json")
    
    mock_get.assert_called_once_with("https://fakeurl.com/games.json", timeout=30)
    mock_process.assert_called_once_with([{"Title": "Mock Game"}], mock_db)


@patch("src.db.ingest.httpx.get")
@patch("src.db.ingest._process_and_insert")
def test_seed_from_url_http_error(mock_process, mock_get):
    """seed_from_url should gracefully catch HTTP errors and not crash."""
    # Simulate a 404 Not Found error
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason_phrase = "Not Found"
    
    # httpx raises HTTPStatusError when raise_for_status() is called on bad codes
    mock_get.side_effect = httpx.HTTPStatusError(
        message="404 Not Found", 
        request=MagicMock(), 
        response=mock_response
    )

    mock_db = MagicMock()
    
    seed_from_url(mock_db, "https://fakeurl.com/missing.json")
    
    mock_process.assert_not_called()
