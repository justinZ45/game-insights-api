from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class Features(BaseModel):
    """Validates the Features section of a game JSON entry."""

    model_config = ConfigDict(populate_by_name=True)

    is_handheld: Optional[bool] = Field(alias="Handheld?", default=None)
    max_players: Optional[int] = Field(alias="Max Players", default=None, ge=1)
    is_multiplatform: Optional[bool] = Field(alias="Multiplatform?", default=None)
    is_online: Optional[bool] = Field(alias="Online?", default=None)
