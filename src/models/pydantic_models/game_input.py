from pydantic import BaseModel, ConfigDict, Field
from .features import Features
from .metadata import Metadata
from .metrics import Metrics
from .release import Release
from .length import Length


class GameInput(BaseModel):
    """Top level validation model for a single game entry in the input JSON file."""

    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(alias="Title")
    features: Features = Field(alias="Features")
    metadata: Metadata = Field(alias="Metadata")
    metrics: Metrics = Field(alias="Metrics")
    release: Release = Field(alias="Release")
    length: Length = Field(alias="Length")
