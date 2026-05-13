from typing import Optional
from pydantic import Field
from src.models.pydantic_models.ingestion.game_input import GameInput
from src.models.pydantic_models.ingestion.features import Features
from src.models.pydantic_models.ingestion.metadata import Metadata
from src.models.pydantic_models.ingestion.metrics import Metrics
from src.models.pydantic_models.ingestion.release import Release
from src.models.pydantic_models.ingestion.length import Length
from src.models.pydantic_models.ingestion.playstyle import PlayStyle
from datetime import datetime


class FeaturesUpdate(Features):
    is_handheld: Optional[bool] = Field(alias="Handheld?", default=None)
    max_players: Optional[int] = Field(alias="Max Players", default=None, ge=1)
    is_multiplatform: Optional[bool] = Field(alias="Multiplatform?", default=None)
    is_online: Optional[bool] = Field(alias="Online?", default=None)

class MetadataUpdate(Metadata):
    genres: Optional[str] = Field(alias="Genres", default=None)
    publishers: Optional[str] = Field(alias="Publishers", default=None)
    is_licensed: Optional[bool] = Field(alias="Licensed?", default=None)
    is_sequel: Optional[bool] = Field(alias="Sequel?", default=None)

class MetricsUpdate(Metrics):
    review_score: Optional[int] = Field(alias="Review Score", default=None, ge=0, le=100)
    sales_millions_usd: Optional[float] = Field(alias="Sales", default=None, ge=0)
    used_price_usd: Optional[float] = Field(alias="Used Price", default=None, ge=0)

class ReleaseUpdate(Release):
    console: Optional[str] = Field(alias="Console", default=None)
    esrb_rating: Optional[str] = Field(alias="Rating", default=None)
    is_re_release: Optional[bool] = Field(alias="Re-release?", default=None)
    release_year: Optional[int] = Field(alias="Year", default=None, ge=1950, le=datetime.now().year)

class PlayStyleUpdate(PlayStyle):
    average: Optional[float] = Field(alias="Average", default=None, ge=0)
    leisure: Optional[float] = Field(alias="Leisure", default=None, ge=0)
    median: Optional[float] = Field(alias="Median", default=None, ge=0)
    polled: Optional[int] = Field(alias="Polled", default=None, ge=0)
    rushed: Optional[float] = Field(alias="Rushed", default=None, ge=0)

class LengthUpdate(Length):
    all_playstyles: Optional[PlayStyleUpdate] = Field(alias="All PlayStyles", default=None)
    completionists: Optional[PlayStyleUpdate] = Field(alias="Completionists", default=None)
    main_extras: Optional[PlayStyleUpdate] = Field(alias="Main + Extras", default=None)
    main_story: Optional[PlayStyleUpdate] = Field(alias="Main Story", default=None)

class GameUpdate(GameInput):
    title: Optional[str] = Field(alias="Title", default=None)
    features: Optional[FeaturesUpdate] = Field(alias="Features", default=None)
    metadata: Optional[MetadataUpdate] = Field(alias="Metadata", default=None)
    metrics: Optional[MetricsUpdate] = Field(alias="Metrics", default=None)
    release: Optional[ReleaseUpdate] = Field(alias="Release", default=None)
    length: Optional[LengthUpdate] = Field(alias="Length", default=None)