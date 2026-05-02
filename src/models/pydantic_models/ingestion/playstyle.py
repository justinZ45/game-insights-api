from pydantic import BaseModel, ConfigDict, Field


class PlayStyle(BaseModel):
    """Represents a single playstyle entry with completion time statistics."""

    model_config = ConfigDict(populate_by_name=True)

    average: float = Field(alias="Average", default=None, ge=0)
    leisure: float = Field(alias="Leisure", default=None, ge=0)
    median: float = Field(alias="Median", default=None, ge=0)
    polled: int = Field(alias="Polled", default=None, ge=0)
    rushed: float = Field(alias="Rushed", default=None, ge=0)
