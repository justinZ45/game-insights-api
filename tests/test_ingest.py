import pytest
from pydantic import ValidationError
from src.models.pydantic_models import GameInput
from src.db.ingest import open_file, clean_data


def test_open_file_missing():
    """open_file should return None when file does not exist."""
    result = open_file("nonexistent_file.json")
    assert result is None


def test_clean_data(sample_game):
    games, _, _ = clean_data([sample_game])
    assert games[0].title == "Super Mario"


def test_clean_data_genre_cache(sample_game):
    """Same genre across two games should produce one cache entry."""
    _, genre_cache, _ = clean_data([sample_game, sample_game])
    assert len(genre_cache) == 1


def test_clean_data_publisher_cache(sample_game):
    """Same publisher across two games should produce one cache entry."""
    _, _, publisher_cache = clean_data([sample_game, sample_game])
    assert len(publisher_cache) == 1


def test_clean_data_invalid_game_skipped():
    """clean_data should skip games that fail Pydantic validation."""
    bad_game = {"Title": "Bad Game"}
    games, _, _ = clean_data([bad_game])
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
