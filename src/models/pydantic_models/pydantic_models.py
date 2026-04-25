from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import datetime
from decimal import Decimal


class Features(BaseModel):
    """Validates the Features section of a game JSON entry."""

    model_config = ConfigDict(populate_by_name=True)

    is_handheld: Optional[bool] = Field(alias="Handheld?", default=None)
    max_players: Optional[int] = Field(alias="Max Players", default=None, ge=1)
    is_multiplatform: Optional[bool] = Field(alias="Multiplatform?", default=None)
    is_online: Optional[bool] = Field(alias="Online?", default=None)


class Metadata(BaseModel):
    """Validates the Metadata section of a game JSON entry."""

    model_config = ConfigDict(populate_by_name=True)

    genres: str = Field(alias="Genres", default=None)
    is_licensed: Optional[bool] = Field(alias="Licensed?", default=None)
    publishers: str = Field(alias="Publishers", default=None)
    is_sequel: Optional[bool] = Field(alias="Sequel?", default=None)


class Metrics(BaseModel):
    """Validates the Metrics section of a game JSON entry."""

    model_config = ConfigDict(populate_by_name=True)

    review_score: Optional[int] = Field(
        alias="Review Score", default=None, ge=0, le=100
    )
    sales_millions_usd: Optional[float] = Field(alias="Sales", default=None, ge=0)
    used_price_usd: Optional[float] = Field(alias="Used Price", default=None, ge=0)

    @field_validator("used_price_usd")
    @classmethod
    def check_decimal_places(cls, price):
        """Validates that entered used price field rating is 2 decimal places, as money amounts can not be more"""
        if price is not None:
            d = Decimal(str(price))
            if d.as_tuple().exponent < -2:
                raise ValueError("Used price must have at most 2 decimal places")
        return price


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


class PlayStyle(BaseModel):
    """Represents a single playstyle entry with completion time statistics."""

    model_config = ConfigDict(populate_by_name=True)

    average: float = Field(alias="Average", default=None, ge=0)
    leisure: float = Field(alias="Leisure", default=None, ge=0)
    median: float = Field(alias="Median", default=None, ge=0)
    polled: int = Field(alias="Polled", default=None, ge=0)
    rushed: float = Field(alias="Rushed", default=None, ge=0)


class Length(BaseModel):
    """Validates the Length section containing all playstyle entries."""

    model_config = ConfigDict(populate_by_name=True)

    all_playstyles: Optional[PlayStyle] = Field(alias="All PlayStyles", default=None)
    completionists: Optional[PlayStyle] = Field(alias="Completionists", default=None)
    main_extras: Optional[PlayStyle] = Field(alias="Main + Extras", default=None)
    main_story: Optional[PlayStyle] = Field(alias="Main Story", default=None)


class Game(BaseModel):
    """Top level validation model for a single game entry in the input JSON file."""

    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(alias="Title")
    features: Features = Field(alias="Features")
    metadata: Metadata = Field(alias="Metadata")
    metrics: Metrics = Field(alias="Metrics")
    release: Release = Field(alias="Release")
    length: Length = Field(alias="Length")
