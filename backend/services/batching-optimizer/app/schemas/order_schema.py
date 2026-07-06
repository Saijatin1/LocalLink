from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class LocationSchema(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    model_config = ConfigDict(from_attributes=True)


class OrderSchema(BaseModel):
    order_id: str

    vendor_location: LocationSchema

    customer_location: LocationSchema

    ready_time: datetime

    preparation_time: int = Field(..., ge=0)

    priority: int = Field(default=1, ge=1, le=5)

    model_config = ConfigDict(from_attributes=True)