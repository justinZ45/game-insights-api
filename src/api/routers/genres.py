from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.models.orm_models import Genre
from src.models.pydantic_models import GenreResponse
from src.api.dependencies import get_db

router = APIRouter(prefix="/genres", tags=["genres"])


@router.get("/", response_model=list[GenreResponse])
def get_all_genres(
    limit: int = 10, offset: int = 0, session: Session = Depends(get_db)
):
    """Returns a list of genres, by any optionally provided filters."""

    query = select(Genre).offset(offset).limit(limit)
    return session.execute(query).scalars().all()


@router.get("/{genre_id}", response_model=GenreResponse)
def get_genre(genre_id: int, session: Session = Depends(get_db)):
    """Returns a single genre by ID."""

    genre = session.get(Genre, genre_id)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre