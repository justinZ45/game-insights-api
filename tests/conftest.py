import pytest


@pytest.fixture
def sample_game():
    return {
        "Title": "Super Mario",
        "Features": {
            "Handheld?": True,
            "Max Players": 1,
            "Multiplatform?": False,
            "Online?": False,
        },
        "Metadata": {
            "Genres": "Action",
            "Licensed?": True,
            "Publishers": "Nintendo",
            "Sequel?": False,
        },
        "Metrics": {"Review Score": 85, "Sales": 4.69, "Used Price": 24.95},
        "Release": {
            "Console": "Nintendo DS",
            "Rating": "E",
            "Re-release?": False,
            "Year": 2004,
        },
        "Length": {
            "Main Story": {
                "Average": 10.0,
                "Leisure": 12.0,
                "Median": 10.0,
                "Polled": 20,
                "Rushed": 8.0,
            }
        },
    }
