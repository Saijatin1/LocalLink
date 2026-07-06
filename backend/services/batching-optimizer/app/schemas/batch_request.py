from pydantic import BaseModel

from app.schemas.order_schema import OrderSchema
from app.schemas.rider_schema import RiderSchema


class BatchRequest(BaseModel):
    orders: list[OrderSchema]
    riders: list[RiderSchema]