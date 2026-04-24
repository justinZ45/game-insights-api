import pytest
from pydantic import ValidationError
from src import GameJsonInput


@pytest.mark.parametrize("year", [1910, 2050])
def test_invalid_year(sample_game, year):
    """GameJsonInput should reject years less than 1950 and above the current year"""
    sample_game["Release"]["Year"] = year

    with pytest.raises(ValidationError):
        GameJsonInput.model_validate(sample_game)
