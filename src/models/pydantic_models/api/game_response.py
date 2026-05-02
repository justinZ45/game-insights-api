from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from .game_length_response import GameLengthResponse


class GameResponse(BaseModel):
    """Response schema for a single game."""

    model_config = ConfigDict(from_attributes=True)

    game_id: int
    title: str
    console: Optional[str]
    review_score: Optional[int]
    release_year: Optional[int]
    esrb_rating: Optional[str]
    esrb_rating: Optional[str]
    is_re_release: Optional[bool]
    sales_millions_usd: Optional[float]
    used_price_usd: Optional[float]
    is_licensed: Optional[bool]
    is_sequel: Optional[bool]
    is_handheld: Optional[bool]
    max_players: Optional[int]
    is_multiplatform: Optional[bool]
    is_online: Optional[bool]
    genres: list[str] = []
    publishers: list[str] = []
    lengths: list[GameLengthResponse] = []

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
