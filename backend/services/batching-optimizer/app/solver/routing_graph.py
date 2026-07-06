from dataclasses import dataclass

from app.models.routing_node import RoutingNode


@dataclass(slots=True)
class RoutingGraph:

    nodes: list[RoutingNode]

    distance_matrix: list[list[int]]

    pickup_delivery_pairs: list[tuple[int, int]]

    depot_indices: list[int]