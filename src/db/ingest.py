import json
from src.models.orm_models import (
    Game,
    Genre,
    Publisher,
    GameGenre,
    GameLength,
    GamePublisher,
)
from src.models.pydantic_models import GameInput
from pydantic import ValidationError
from sqlalchemy import select
import httpx




def seed_from_url(db, url):
    """Fetches and ingests game data from specified url ."""
    try:
        print(f"Fetching data from url: {url}", flush=True)
        response = httpx.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        print(f"Fetched {len(data)} records - ingesting...", flush=True)
        _process_and_insert(data, db)

    except httpx.TimeoutException:
        print("Url fetch timed out after 30 seconds. Check network connection!")
    except httpx.HTTPStatusError as e:
        print(
            f"Url returned an error response: {e.response.status_code} {e.response.reason_phrase}"
        )
    except httpx.RequestError as e:
        print(f"Network error fetching from url: {type(e).__name__}: {e}")
    except Exception as e:
        print(f"Unexpected error during url seed: {type(e).__name__}: {e}")


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


def clean_data(data, genre_cache, publisher_cache):
    """
    Parses and cleans raw JSON game data into ORM model objects.
    Returns a list of Game objects with nested lengths, genres, and publishers.
    """

    games = []

    for game in data:
        try:
            game = GameInput.model_validate(
                game, by_alias=True
            )  # validate game dict using pydantic model

        except ValidationError as e:
            title = (
                game.get("Title", "Unknown") if isinstance(game, dict) else "Unknown"
            )
            print(f"Skipping invalid game, title: {title}: {e}")
            continue

        game_obj = Game(
            title=game.title,
            is_handheld=game.features.is_handheld,
            max_players=game.features.max_players,
            is_multiplatform=game.features.is_multiplatform,
            is_online=game.features.is_online,
            is_licensed=game.metadata.is_licensed,
            is_sequel=game.metadata.is_sequel,
            review_score=game.metrics.review_score,
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

        # Normalize genres and manage links
        genres_raw = game.metadata.genres.replace("/", ",").split(",")
        genres_raw = [g.strip() for g in genres_raw if g.strip()]

        for genre_name in genres_raw:
            if genre_name not in genre_cache:
                # This is a genuinely new genre not present in JSON or DB yet
                genre_cache[genre_name] = Genre(name=genre_name)

            # Link via junction table object
            game_obj.genres.append(GameGenre(genre=genre_cache[genre_name]))

        # Normalize publishers and manage links
        publishers_raw = game.metadata.publishers.replace("/", ",").split(",")
        publishers_raw = [p.strip() for p in publishers_raw if p.strip()]

        for publisher_name in publishers_raw:
            if publisher_name not in publisher_cache:
                # This is a genuinely new publisher not present in JSON or DB yet
                publisher_cache[publisher_name] = Publisher(name=publisher_name)

            # Link via junction table object
            game_obj.publishers.append(
                GamePublisher(publisher=publisher_cache[publisher_name])
            )

        games.append(game_obj)

    return games


def insert_games(games, genre_cache, publisher_cache, db):
    """
    Inserts all games and new lookup parameters into the database.
    Only updates lookup tables with records missing database PK identifiers.
    """
    with db.transaction() as session:
        # Only add records that DO NOT have a primary key yet (meaning they are brand new)
        for genre in genre_cache.values():
            if genre.genre_id is None:
                session.add(genre)

        for publisher in publisher_cache.values():
            if publisher.publisher_id is None:
                session.add(publisher)

        # Flush ensures new lookups get IDs from Postgres before games link to them
        session.flush()

        for game in games:
            session.add(game)


def ingest_file_data(filepath, db):
    """Ingests game data from a local JSON file."""
    try:
        data = open_file(filepath)
        if data is None:
            print(f"Ingestion aborted - could not load file: {filepath}")
            return
        _process_and_insert(data, db)
    except Exception as e:
        print(f"Ingestion failed: {type(e).__name__}: {e}")
        raise


def _process_and_insert(data, db):
    """Shared pipeline - cleans and inserts game data regardless of source."""
    if not data:
        print("No data to process - aborting.")
        return

    try:
        print(f"Processing {len(data)} games...", flush=True)

        # Hydrate caches directly from the live database records
        genre_cache = {}
        publisher_cache = {}

        with db.get_session() as session:
            existing_genres = session.scalars(select(Genre)).all()
            for g in existing_genres:
                genre_cache[g.name] = g

            existing_publishers = session.scalars(select(Publisher)).all()
            for p in existing_publishers:
                publisher_cache[p.name] = p

        # Clean using the pre-loaded dictionary caches
        games = clean_data(data, genre_cache, publisher_cache)

        # Run database insertions
        insert_games(games, genre_cache, publisher_cache, db)
        print(f"Successfully inserted {len(games)} games.", flush=True)

    except Exception as e:
        print(f"Failed during clean/insert pipeline: {type(e).__name__}: {e}")
        raise
