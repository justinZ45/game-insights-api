from pydantic import BaseModel, ConfigDict
from typing import Optional


class GameLengthResponse(BaseModel):
    """Response schema for a single game length object."""

    model_config = ConfigDict(from_attributes=True)

    game_lengths_id: int
    playstyle: Optional[str]
    avg_hours: Optional[float]
    leisure_hours: Optional[float]
    median_hours: Optional[float]
    rushed_hours: Optional[float]
    num_players_polled: Optional[int]
