import json
from db import Game, GameLength, Genre, Publisher, GameGenre, GamePublisher
from sqlalchemy.exc import OperationalError


def open_file(filename: str):
    """Opens a JSON file and loads its data."""

    try:
        with open(filename) as f:
            data = json.load(f)
        return data

    except FileNotFoundError:
        print(f"File {filename} not found. ")
    except IsADirectoryError:
        print(f"{filename} is a directory. Please enter a file path.")
    except ValueError as e:
        print(f"Error: Data mismatch or malformed JSON. {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def clean_data(data):
    """
    Parses and cleans raw JSON game data into ORM model objects.
    Returns a list of Game objects with nested lengths, genres, and publishers.
    """

    ESRB_RATINGS = ("E", "M", "T", "A")
    games = []
    genre_cache = {}  # avoid duplicate genre lookups: {name: Genre object}
    publisher_cache = {}  # avoid duplicate publisher lookups: {name: Publisher object}

    for game in data:
        # clean core game fields
        review_score = game["Metrics"]["Review Score"]
        review_score = max(0, min(100, review_score))  # clip between 0 and 100

        # ensure rating adheres to ESRB standards, default to RP (rating pending) if unknown
        esrb = str(game["Release"]["Rating"]).upper().strip()
        esrb = esrb if esrb in ESRB_RATINGS else "RP"

        game_obj = Game(
            title=game["Title"],
            is_handheld=game["Features"]["Handheld?"],
            max_players=game["Features"]["Max Players"],
            is_multiplatform=game["Features"]["Multiplatform?"],
            is_online=game["Features"]["Online?"],
            is_licensed=game["Metadata"]["Licensed?"],
            is_sequel=game["Metadata"]["Sequel?"],
            review_score=review_score,
            sales_millions_usd=game["Metrics"]["Sales"],
            used_price_usd=game["Metrics"]["Used Price"],
            console=game["Release"]["Console"],
            esrb_rating=esrb,
            is_re_release=game["Release"]["Re-release?"],
            release_year=game["Release"]["Year"],
        )

        # nest lengths directly on game object, set game_id FK automatically on flush
        for length_type, values in game["Length"].items():
            length_obj = GameLength(
                playstyle=length_type,
                avg_hours=round(values["Average"], 2),
                leisure_hours=round(values["Leisure"], 2),
                median_hours=round(values["Median"], 2),
                rushed_hours=round(values["Rushed"], 2),
                num_players_polled=values["Polled"],
            )
            game_obj.lengths.append(length_obj)

        # normalize genre separators '/' and filter out empty strings
        genres_raw = game["Metadata"]["Genres"].replace("/", ",").split(",")
        genres_raw = [g.strip() for g in genres_raw if g.strip()]

        for genre_name in genres_raw:
            # get or create, reuse existing Genre object if already seen across games (table will hold unique genres)
            genre_name = genre_name.strip()
            if genre_name not in genre_cache:
                genre_cache[genre_name] = Genre(name=genre_name)
            game_obj.genres.append(GameGenre(genre=genre_cache[genre_name]))

        # normalize publisher separators and filter empty strings
        publishers_raw = game["Metadata"]["Publishers"].replace("/", ",").split(",")
        publishers_raw = [p.strip() for p in publishers_raw if p.strip()]
        for publisher_name in publishers_raw:
            # get or create, reuse existing Publisher object if already seen across games (table will hold unique publishers)
            publisher_name = publisher_name.strip()
            if publisher_name not in publisher_cache:
                publisher_cache[publisher_name] = Publisher(name=publisher_name)
            game_obj.publishers.append(
                GamePublisher(publisher=publisher_cache[publisher_name])
            )

        games.append(game_obj)

    return games, genre_cache, publisher_cache


def insert_games(games, genre_cache, publisher_cache, db):
    """
    Inserts all games and related objects into the database.
    Genres and publishers are inserted first to generate IDs before junction rows are created.
    All operations run in a single transaction, commits on success, rolls back on failure.
    """
    try:
        with db.get_session() as session:
            for genre in genre_cache.values():
                session.add(genre)

            for publisher in publisher_cache.values():
                session.add(publisher)

            session.flush()
            for game in games:
                session.add(game)
                session.flush()

            session.commit()
            print(f"Successfully inserted {len(games)} games!")

    except OperationalError:
        print("Could not connect to db. Is Docker running?")
    except Exception as e:
        print(f"An unexpected error occurred during insert: {e}")


def ingest_data(filename, db):
    """Entry point for the ingest pipeline. Loads, cleans, and inserts game data from CORGIS JSON file."""
    games, genre_cache, publisher_cache = clean_data(open_file(filename))
    insert_games(games, genre_cache, publisher_cache, db)
