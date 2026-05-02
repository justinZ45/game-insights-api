from pydantic import BaseModel, ConfigDict


class PublisherResponse(BaseModel):
    """Response schema for a single publisher."""

    model_config = ConfigDict(from_attributes=True)

    publisher_id: int
    name: str
