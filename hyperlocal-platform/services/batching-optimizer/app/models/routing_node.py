from dataclasses import dataclass

from app.models.order import Location


@dataclass(slots=True)
class RoutingNode:

    node_id: int

    order_id: str | None

    location: Location

    is_depot: bool

    is_pickup: bool

    demand: int