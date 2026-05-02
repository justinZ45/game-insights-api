from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime


class Release(BaseModel):
    """Validates the Release section of a game JSON entry."""

    model_config = ConfigDict(populate_by_name=True)

    console: Optional[str] = Field(alias="Console", default=None)
    esrb_rating: Optional[str] = Field(alias="Rating", default=None)
    is_re_release: Optional[bool] = Field(alias="Re-release?", default=None)
    release_year: Optional[int] = Field(
        alias="Year", default=None, ge=1950, le=datetime.now().year
    )

    @field_validator("esrb_rating")
    @classmethod
    def validate_esrb_rating(cls, rating):
        """Validates that entered ESRB rating matches all possible values. Default to 'RP' otherwise"""

        ESRB_RATINGS = ("E", "M", "T", "A", "RP", "E10+")
        if rating is not None:
            rating = str(rating).upper().strip()
            return rating if rating in ESRB_RATINGS else "RP"
        return "RP"  # default to RP if None
