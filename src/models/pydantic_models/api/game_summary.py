from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional


class GameSummary(BaseModel):
    """Lightweight game response for list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    game_id: int
    title: str
    console: Optional[str]
    review_score: Optional[int]
    release_year: Optional[int]
    esrb_rating: Optional[str]
    genres: list[str] = []
    publishers: list[str] = []

    @field_validator("genres", mode="before")
    @classmethod
    def serialize_genres(cls, v):
        # If the input is a list of ORM objects, extract the names
        if isinstance(v, list) and v and not isinstance(v[0], str):
            return [g.genre.name for g in v]
        return v

    @field_validator("publishers", mode="before")
    @classmethod
    def serialize_publishers(cls, v):
        # If the input is a list of ORM objects, extract the names
        if isinstance(v, list) and v and not isinstance(v[0], str):
            return [g.publisher.name for g in v]
        return v
