from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from src.models.orm_models import (
    Game,
    GameLength,
    GameGenre,
    GamePublisher,
    Genre,
    Publisher,
)
from src.models.pydantic_models import GameResponse, GameInput, GameSummary, GameUpdate
from src.api.dependencies import get_db


router = APIRouter(prefix="/games", tags=["games"])


@router.get("/", response_model=list[GameSummary])
def get_all_games(
    console: Optional[str] = None,
    genre: Optional[str] = None,
    publisher: Optional[str] = None,
    min_review_score: Optional[int] = None,
    max_review_score: Optional[int] = None,
    min_players: Optional[int] = None,
    max_players: Optional[int] = None,
    min_release_year: Optional[int] = None,
    max_release_year: Optional[int] = None,
    limit: int = 10,
    offset: int = 0,
    session: Session = Depends(get_db),
):
    """Returns a lightweight list of games with optional filters."""

    conditions = []

    if console:
        conditions.append(Game.console == console)
    if genre:
        conditions.append(Game.genres.any(GameGenre.genre.has(Genre.name == genre)))
    if publisher:
        conditions.append(
            Game.publishers.any(
                GamePublisher.publisher.has(Publisher.name == publisher)
            )
        )
    if min_review_score is not None:
        conditions.append(Game.review_score >= min_review_score)
    if max_review_score is not None:
        conditions.append(Game.review_score <= max_review_score)
    if min_players is not None:
        conditions.append(Game.max_players >= min_players)
    if max_players is not None:
        conditions.append(Game.max_players <= max_players)
    if min_release_year is not None:
        conditions.append(Game.release_year >= min_release_year)
    if max_release_year is not None:
        conditions.append(Game.release_year <= max_release_year)

    query = select(Game).options(
        selectinload(Game.genres),
        selectinload(Game.publishers),
    )

    if conditions:
        query = query.where(*conditions)

    query = query.offset(offset).limit(limit)
    return session.execute(query).scalars().all()


@router.get("/{game_id}", response_model=GameResponse)
def get_game(game_id: int, session: Session = Depends(get_db)):
    """Returns a single game by ID with full details including lengths."""

    game = session.execute(
        select(Game)
        .options(
            selectinload(Game.genres),
            selectinload(Game.publishers),
            selectinload(Game.lengths),
        )
        .where(Game.game_id == game_id)
    ).scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.delete("/{game_id}", status_code=204)
def delete_game(game_id: int, session: Session = Depends(get_db)):
    """Deletes a single game by ID. Cascades to lengths, genres, and publishers."""

    game = session.get(Game, game_id)

    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

    try:
        session.delete(game)
        session.commit()
    except SQLAlchemyError:
        session.rollback()

        raise HTTPException(
            status_code=500,
            detail="An unexpected database error occurred while trying to delete the game.",
        )


@router.post("/", response_model=GameResponse, status_code=201)
def create_game(game_data: GameInput, session: Session = Depends(get_db)):
    """
    Creates a new game.
    Accepts your existing validated nested JSON (GameInput), unpacks it,
    and returns a clean, flattened GameResponse.
    """
    # Prevent
    existing_game = session.execute(
        select(Game).where(
            Game.title == game_data.title, Game.console == game_data.release.console
        )
    ).scalar_one_or_none()

    if existing_game:
        raise HTTPException(
            status_code=409,
            detail=f"Game '{game_data.title}' on '{game_data.release.console}' already exists.",
        )

    try:
        # Map nested Pydantic models directly to the flat Game ORM Model
        new_game = Game(
            title=game_data.title,
            is_handheld=game_data.features.is_handheld,
            max_players=game_data.features.max_players,
            is_multiplatform=game_data.features.is_multiplatform,
            is_online=game_data.features.is_online,
            is_licensed=game_data.metadata.is_licensed,
            is_sequel=game_data.metadata.is_sequel,
            review_score=game_data.metrics.review_score,
            sales_millions_usd=game_data.metrics.sales_millions_usd,
            used_price_usd=game_data.metrics.used_price_usd,
            console=game_data.release.console,
            esrb_rating=game_data.release.esrb_rating,
            is_re_release=game_data.release.is_re_release,
            release_year=game_data.release.release_year,
        )

        session.add(new_game)
        session.flush()  # Generates the game_id in PostgreSQL

        # Associate/Create Genres
        if game_data.metadata.genres:
            genre_names = [
                g.strip() for g in game_data.metadata.genres.split(",") if g.strip()
            ]
            for name in genre_names:
                genre = session.execute(
                    select(Genre).where(Genre.name == name)
                ).scalar_one_or_none()
                if not genre:
                    genre = Genre(name=name)
                    session.add(genre)
                    session.flush()
                session.add(
                    GameGenre(game_id=new_game.game_id, genre_id=genre.genre_id)
                )

        # Associate/Create Publishers
        if game_data.metadata.publishers:
            pub_names = [
                p.strip() for p in game_data.metadata.publishers.split(",") if p.strip()
            ]
            for name in pub_names:
                publisher = session.execute(
                    select(Publisher).where(Publisher.name == name)
                ).scalar_one_or_none()
                if not publisher:
                    publisher = Publisher(name=name)
                    session.add(publisher)
                    session.flush()
                session.add(
                    GamePublisher(
                        game_id=new_game.game_id, publisher_id=publisher.publisher_id
                    )
                )

        # Populate Game Lengths (
        playstyles_map = {
            "All PlayStyles": game_data.length.all_playstyles,
            "Completionists": game_data.length.completionists,
            "Main + Extras": game_data.length.main_extras,
            "Main Story": game_data.length.main_story,
        }

        for display_name, playstyle_data in playstyles_map.items():
            if playstyle_data is not None:
                length_entry = GameLength(
                    game_id=new_game.game_id,
                    playstyle=display_name,
                    avg_hours=playstyle_data.average,
                    leisure_hours=playstyle_data.leisure,
                    median_hours=playstyle_data.median,
                    rushed_hours=playstyle_data.rushed,
                    num_players_polled=playstyle_data.polled,
                )
                session.add(length_entry)

        session.commit()
        session.refresh(new_game)
        return new_game

    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(
            status_code=500, detail=f"An unexpected database error occurred: {str(e)}"
        )



@router.patch("/{game_id}", response_model=GameResponse)
def update_game(game_id: int, update_data: GameUpdate, session: Session = Depends(get_db)):
    """Partially updates an existing game and its nested properties dynamically."""
    
    game = session.execute(
        select(Game).options(
            selectinload(Game.genres),
            selectinload(Game.publishers),
            selectinload(Game.lengths),
        ).where(Game.game_id == game_id)
    ).scalar_one_or_none()

    if not game:
        raise HTTPException(status_code=404, detail=f"Game {game_id} not found")

    try:
        # Update Title directly
        if update_data.title is not None:
            game.title = update_data.title

        # Update Features 
        if update_data.features:
            for key, val in update_data.features.model_dump(exclude_unset=True).items():
                col_name = f"is_{key}" if hasattr(game, f"is_{key}") else key
                setattr(game, col_name, val)

        # Update Metrics 
        for sub_model in [update_data.metrics, update_data.release]:
            if sub_model:
                for key, val in sub_model.model_dump(exclude_unset=True).items():
                    setattr(game, key, val)

        # Update Metadata
        if update_data.metadata:
            meta_dict = update_data.metadata.model_dump(exclude_unset=True)
            
            if "is_licensed" in meta_dict: game.is_licensed = meta_dict["is_licensed"]
            if "is_sequel" in meta_dict: game.is_sequel = meta_dict["is_sequel"]

            # Rewrite Genres if provided
            if "genres" in meta_dict and meta_dict["genres"] is not None:
                game.genres.clear()
                session.flush()
                for name in [g.strip() for g in meta_dict["genres"].split(",") if g.strip()]:
                    genre = session.execute(select(Genre).where(Genre.name == name)).scalar_one_or_none() or Genre(name=name)
                    game.genres.append(GameGenre(genre_id=genre.genre_id if genre.genre_id else session.add(genre) or session.flush() or genre.genre_id))

            # Rewrite Publishers if provided
            if "publishers" in meta_dict and meta_dict["publishers"] is not None:
                game.publishers.clear()
                session.flush()
                for name in [p.strip() for p in meta_dict["publishers"].split(",") if p.strip()]:
                    pub = session.execute(select(Publisher).where(Publisher.name == name)).scalar_one_or_none() or Publisher(name=name)
                    game.publishers.append(GamePublisher(publisher_id=pub.publisher_id if pub.publisher_id else session.add(pub) or session.flush() or pub.publisher_id))

        # Update Playstyle Lengths 
        if update_data.length:
            playstyles_map = {
                "All PlayStyles": update_data.length.all_playstyles,
                "Completionists": update_data.length.completionists,
                "Main + Extras": update_data.length.main_extras,
                "Main Story": update_data.length.main_story,
            }
            # Map Pydantic fields to actual database column names
            len_map = {"average": "avg_hours", "leisure": "leisure_hours", "median": "median_hours", "rushed": "rushed_hours", "polled": "num_players_polled"}

            for display_name, playstyle_data in playstyles_map.items():
                if playstyle_data is not None:
                    existing_length = next((l for l in game.lengths if l.playstyle == display_name), None)
                    fields = playstyle_data.model_dump(exclude_unset=True)
                    
                    if existing_length:
                        for pydantic_key, db_col in len_map.items():
                            if pydantic_key in fields:
                                setattr(existing_length, db_col, fields[pydantic_key])
                    else:
                        session.add(GameLength(
                            game_id=game.game_id, playstyle=display_name,
                            avg_hours=fields.get("average"), leisure_hours=fields.get("leisure"),
                            median_hours=fields.get("median"), rushed_hours=fields.get("rushed"),
                            num_players_polled=fields.get("polled")
                        ))

        session.commit()
        session.refresh(game)
        return game

    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")