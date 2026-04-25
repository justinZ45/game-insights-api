from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from .playstyle import PlayStyle


class Length(BaseModel):
    """Validates the Length section containing all playstyle entries."""

    model_config = ConfigDict(populate_by_name=True)

    all_playstyles: Optional[PlayStyle] = Field(alias="All PlayStyles", default=None)
    completionists: Optional[PlayStyle] = Field(alias="Completionists", default=None)
    main_extras: Optional[PlayStyle] = Field(alias="Main + Extras", default=None)
    main_story: Optional[PlayStyle] = Field(alias="Main Story", default=None)
