from ortools.constraint_solver import pywrapcp


class SolverConstraints:

    @staticmethod
    def add_capacity_dimension(
        routing: pywrapcp.RoutingModel,
        demand_callback_index: int,
        capacities: list[int],
    ):
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,
            capacities,
            True,
            "Capacity",
        )

    @staticmethod
    def add_pickup_delivery_constraints(
        routing: pywrapcp.RoutingModel,
        manager: pywrapcp.RoutingIndexManager,
        distance_dimension: pywrapcp.RoutingDimension,
        pickup_delivery_pairs: list[tuple[int, int]],
    ):

        for pickup, delivery in pickup_delivery_pairs:

            pickup_index = manager.NodeToIndex(pickup)
            delivery_index = manager.NodeToIndex(delivery)

            routing.AddPickupAndDelivery(
                pickup_index,
                delivery_index,
            )

            routing.solver().Add(
                routing.VehicleVar(pickup_index)
                ==
                routing.VehicleVar(delivery_index)
            )

            routing.solver().Add(
                distance_dimension.CumulVar(pickup_index)
                <=
                distance_dimension.CumulVar(delivery_index)
            )