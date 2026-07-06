from app.models.order import Location
from app.models.routing_node import RoutingNode
from app.solver.distance_matrix import DistanceMatrixBuilder

nodes = [
    RoutingNode(
        node_id=0,
        order_id="O1",
        location=Location(17.450, 78.390),
        is_depot=False,
        is_pickup=True,
        demand=1,
    ),
    RoutingNode(
        node_id=1,
        order_id="O1",
        location=Location(17.460, 78.410),
        is_depot=False,
        is_pickup=False,
        demand=-1,
    ),
    RoutingNode(
        node_id=2,
        order_id="O2",
        location=Location(17.470, 78.420),
        is_depot=False,
        is_pickup=True,
        demand=1,
    ),
]

matrix = DistanceMatrixBuilder.build(nodes)

for row in matrix:
    print(row)