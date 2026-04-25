from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class Metadata(BaseModel):
    """Validates the Metadata section of a game JSON entry."""

    model_config = ConfigDict(populate_by_name=True)

    genres: str = Field(alias="Genres", default=None)
    is_licensed: Optional[bool] = Field(alias="Licensed?", default=None)
    publishers: str = Field(alias="Publishers", default=None)
    is_sequel: Optional[bool] = Field(alias="Sequel?", default=None)
