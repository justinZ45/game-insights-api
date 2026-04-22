import json
from db import Game, GameLength, Genre, Publisher, GameGenre, GamePublisher
from sqlalchemy.exc import OperationalError
from src import GameJsonInput
from pydantic import ValidationError


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
        try:
            game = GameJsonInput.model_validate(
                game, by_alias=True
            )  # validate game dict using pydantic model

        except ValidationError as e:
            title = (
                game.get("Title", "Unknown") if isinstance(game, dict) else "Unknown"
            )
            print(f"Skipping invalid game, title: {title}: {e}")
            continue

        # clean core game fields
        review_score = game.metrics.review_score
        review_score = max(0, min(100, review_score))  # clip between 0 and 100

        # ensure rating adheres to ESRB standards, default to RP (rating pending) if unknown
        esrb = str(game.release.esrb_rating).upper().strip()
        esrb = esrb if esrb in ESRB_RATINGS else "RP"

        game_obj = Game(
            title=game.title,
            is_handheld=game.features.is_handheld,
            max_players=game.features.max_players,
            is_multiplatform=game.features.is_multiplatform,
            is_online=game.features.is_online,
            is_licensed=game.metadata.is_licensed,
            is_sequel=game.metadata.is_sequel,
            review_score=review_score,
            sales_millions_usd=game.metrics.sales_millions_usd,
            used_price_usd=game.metrics.used_price_usd,
            console=game.release.console,
            esrb_rating=game.release.esrb_rating,
            is_re_release=game.release.is_re_release,
            release_year=game.release.release_year,
        )

        # nest lengths directly on game object, set game_id FK automatically on flush
        for length_type, playstyle in game.length.model_dump(by_alias=True).items():
            if playstyle:  # skip None playstyles
                length_obj = GameLength(
                    playstyle=length_type,
                    avg_hours=round(playstyle["Average"], 2),
                    leisure_hours=round(playstyle["Leisure"], 2),
                    median_hours=round(playstyle["Median"], 2),
                    rushed_hours=round(playstyle["Rushed"], 2),
                    num_players_polled=playstyle["Polled"],
                )
                game_obj.lengths.append(length_obj)

        # normalize genre separators '/' and filter out empty strings
        genres_raw = game.metadata.genres.replace("/", ",").split(",")
        genres_raw = [g.strip() for g in genres_raw if g.strip()]

        for genre_name in genres_raw:
            # get or create, reuse existing Genre object if already seen across games (table will hold unique genres)
            genre_name = genre_name.strip()
            if genre_name not in genre_cache:
                genre_cache[genre_name] = Genre(name=genre_name)
            game_obj.genres.append(GameGenre(genre=genre_cache[genre_name]))

        # normalize publisher separators and filter empty strings
        publishers_raw = game.metadata.publishers.replace("/", ",").split(",")
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
    with db.transaction() as session:
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


def ingest_data(filename, db):
    """Entry point for the ingest pipeline. Loads, cleans, and inserts game data from CORGIS JSON file."""
    games, genre_cache, publisher_cache = clean_data(open_file(filename))
    insert_games(games, genre_cache, publisher_cache, db)
