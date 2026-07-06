from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Location:
    latitude: float
    longitude: float


@dataclass(slots=True)
class Order:
    order_id: str

    vendor_location: Location

    customer_location: Location

    ready_time: datetime

    preparation_time: int

    priority: int = 1

    demand: int = 1