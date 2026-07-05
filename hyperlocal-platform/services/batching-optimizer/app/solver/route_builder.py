from app.models.order import Order
from app.models.rider import Rider
from app.models.routing_node import RoutingNode


class RouteBuilder:

    @staticmethod
    def build(
        riders: list[Rider],
        orders: list[Order],
    ) -> tuple[
        list[RoutingNode],
        list[tuple[int, int]],
        list[int],
    ]:

        nodes = []

        pickup_delivery_pairs = []

        depots = []

        node_index = 0

        for rider in riders:

            depots.append(node_index)

            nodes.append(
                RoutingNode(
                    node_id=node_index,
                    order_id=None,
                    location=rider.current_location,
                    is_depot=True,
                    is_pickup=False,
                    demand=0,
                )
            )

            node_index += 1

        for order in orders:

            pickup = node_index

            nodes.append(
                RoutingNode(
                    node_id=node_index,
                    order_id=order.order_id,
                    location=order.vendor_location,
                    is_depot=False,
                    is_pickup=True,
                    demand=1,
                )
            )

            node_index += 1

            delivery = node_index

            nodes.append(
                RoutingNode(
                    node_id=node_index,
                    order_id=order.order_id,
                    location=order.customer_location,
                    is_depot=False,
                    is_pickup=False,
                    demand=-1,
                )
            )

            node_index += 1

            pickup_delivery_pairs.append(
                (
                    pickup,
                    delivery,
                )
            )

        return (
            nodes,
            pickup_delivery_pairs,
            depots,
        )