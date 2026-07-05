from pydantic import BaseModel, Field, ConfigDict

from app.schemas.order_schema import LocationSchema


class RiderSchema(BaseModel):
    rider_id: str

    current_location: LocationSchema

    capacity: int = Field(..., gt=0)

    current_load: int = Field(..., ge=0)

    available: bool = True

    model_config = ConfigDict(from_attributes=True)