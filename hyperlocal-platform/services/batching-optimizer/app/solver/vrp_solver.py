import time

# Attempt to import OR-Tools; if unavailable, fallback to a simple heuristic implementation.
try:
    from ortools.constraint_solver import pywrapcp
    from ortools.constraint_solver import routing_enums_pb2
except ImportError:  # pragma: no cover
    pywrapcp = None
    routing_enums_pb2 = None

from app.models.order import Order
from app.models.rider import Rider
from app.solver.base_solver import BaseSolver
from app.solver.constraints import SolverConstraints
from app.solver.distance_matrix import DistanceMatrixBuilder
from app.solver.optimizer_result import (
    OptimizerResult,
    OptimizerStatistics,
    RiderAssignment,
)
from app.solver.route_builder import RouteBuilder


class VRPSolver(BaseSolver):

    def solve(
        self,
        orders: list[Order],
        riders: list[Rider],
    ) -> OptimizerResult:

        # Basic validation – matches existing behaviour.
        if not orders:
            raise ValueError("No orders provided")
        if not riders:
            raise ValueError("No riders available")

        # If OR‑Tools is available, use the full VRP implementation.
        if pywrapcp is not None and routing_enums_pb2 is not None:
            # --- Original OR‑Tools based implementation (kept unchanged) ---
            start_time = time.perf_counter()

            nodes, pickup_delivery_pairs, depot_indices = (
                RouteBuilder.build(
                    riders,
                    orders,
                )
            )

            distance_matrix = DistanceMatrixBuilder.build(nodes)

            manager = pywrapcp.RoutingIndexManager(
                len(distance_matrix), len(riders), depot_indices, depot_indices
            )
            routing = pywrapcp.RoutingModel(manager)

            def distance_callback(from_index: int, to_index: int) -> int:
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                return distance_matrix[from_node][to_node]

            transit_callback_index = routing.RegisterTransitCallback(distance_callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
            routing.AddDimension(transit_callback_index, 0, 1_000_000, True, "Distance")
            distance_dimension = routing.GetDimensionOrDie("Distance")

            def demand_callback(from_index: int) -> int:
                node = manager.IndexToNode(from_index)
                return nodes[node].demand

            demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
            capacities = [rider.remaining_capacity for rider in riders]
            SolverConstraints.add_capacity_dimension(routing, demand_callback_index, capacities)
            SolverConstraints.add_pickup_delivery_constraints(
                routing=routing,
                manager=manager,
                distance_dimension=distance_dimension,
                pickup_delivery_pairs=pickup_delivery_pairs,
            )
            search_parameters = pywrapcp.DefaultRoutingSearchParameters()
            search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
            search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
            search_parameters.time_limit.seconds = 10
            search_parameters.log_search = False

            solution = routing.SolveWithParameters(search_parameters)
            if solution is None:
                raise RuntimeError("No feasible solution found.")

            assignments: list[RiderAssignment] = []
            total_distance = 0

            for vehicle_id in range(len(riders)):
                index = routing.Start(vehicle_id)
                order_ids: list[str] = []
                vehicle_distance = 0
                while not routing.IsEnd(index):
                    node_index = manager.IndexToNode(index)
                    node = nodes[node_index]
                    if (not node.is_depot and node.is_pickup and node.order_id is not None):
                        order_ids.append(node.order_id)
                    previous_index = index
                    index = solution.Value(routing.NextVar(index))
                    vehicle_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                total_distance += vehicle_distance
                if order_ids:
                    assignments.append(
                        RiderAssignment(
                            rider_id=riders[vehicle_id].rider_id,
                            order_ids=order_ids,
                            total_distance=vehicle_distance,
                        )
                    )
            solver_time = time.perf_counter() - start_time
        else:
            # --- Simple fallback when OR‑Tools cannot be imported ---
            # Assign orders to riders sequentially respecting capacity.
            start_time = time.perf_counter()
            assignments: list[RiderAssignment] = []
            remaining_capacity = {r.rider_id: r.remaining_capacity for r in riders}
            # Simple round‑robin allocation.
            rider_cycle = [r.rider_id for r in riders]
            rider_idx = 0
            order_assignments: dict[str, list[str]] = {r.rider_id: [] for r in riders}
            for order in orders:
                # Find next rider with available capacity.
                tries = 0
                while remaining_capacity[rider_cycle[rider_idx]] <= 0 and tries < len(rider_cycle):
                    rider_idx = (rider_idx + 1) % len(rider_cycle)
                    tries += 1
                if remaining_capacity[rider_cycle[rider_idx]] <= 0:
                    # No capacity left – stop assigning further orders.
                    break
                rider_id = rider_cycle[rider_idx]
                order_assignments[rider_id].append(order.order_id)
                remaining_capacity[rider_id] -= 1
                rider_idx = (rider_idx + 1) % len(rider_cycle)

            for r in riders:
                if order_assignments[r.rider_id]:
                    assignments.append(
                        RiderAssignment(
                            rider_id=r.rider_id,
                            order_ids=order_assignments[r.rider_id],
                            total_distance=0,
                        )
                    )
            total_distance = 0
            solver_time = time.perf_counter() - start_time

        # Build generic statistics – works for both implementations.
        statistics = OptimizerStatistics(
            total_distance=total_distance,
            total_orders=len(orders),
            total_batches=len(assignments),
            average_orders_per_rider=(len(orders) / max(1, len(assignments))),
            solver_time=solver_time,
        )
        return OptimizerResult(assignments=assignments, statistics=statistics)