from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from typing import Optional
from src.models.orm_models import Game, Publisher, Genre, GameGenre, GamePublisher
from src.models.pydantic_models import GameResponse, GameSummary
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
