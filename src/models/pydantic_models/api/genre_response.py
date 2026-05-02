from pydantic import BaseModel, ConfigDict


class GenreResponse(BaseModel):
    """Response schema for a single genre."""

    model_config = ConfigDict(from_attributes=True)

    genre_id: int
    name: str
