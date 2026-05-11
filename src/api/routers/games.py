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
from src.models.pydantic_models import GameResponse, GameInput, GameSummary
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
