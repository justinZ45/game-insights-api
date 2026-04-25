from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from decimal import Decimal


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
