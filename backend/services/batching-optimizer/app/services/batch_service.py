from datetime import datetime
from app.models.order import Order, Location
from app.models.rider import Rider
from app.schemas.batch_request import BatchRequest
from app.solver.nearest_neighbor import NearestNeighborSolver
from app.solver.vrp_solver import VRPSolver
from app.solver.optimizer_result import OptimizerResult


class BatchService:

    @staticmethod
    def validate_riders(riders: list[Rider]) -> None:
        if not riders:
            raise ValueError("At least one available rider is required.")
        for r in riders:
            if r.capacity <= 0:
                raise ValueError(f"Rider {r.rider_id} must have capacity > 0.")
            if r.current_load < 0:
                raise ValueError(f"Rider {r.rider_id} has invalid current load.")

    @staticmethod
    def validate_orders(orders: list[Order]) -> None:
        if not orders:
            raise ValueError("At least one order is required.")
        for o in orders:
            if o.preparation_time < 0:
                raise ValueError(f"Order {o.order_id} has invalid preparation time.")
            if not (1 <= o.priority <= 5):
                raise ValueError(f"Order {o.order_id} has invalid priority.")

    def run_optimization(
        self,
        request: BatchRequest,
        algorithm: str = "vrp",
    ) -> OptimizerResult:
        # Convert request schemas to domain models
        domain_riders = []
        for r in request.riders:
            if r.available:
                domain_riders.append(
                    Rider(
                        rider_id=r.rider_id,
                        current_location=Location(
                            latitude=r.current_location.latitude,
                            longitude=r.current_location.longitude,
                        ),
                        capacity=r.capacity,
                        current_load=r.current_load,
                        available=r.available,
                    )
                )

        domain_orders = []
        for o in request.orders:
            domain_orders.append(
                Order(
                    order_id=o.order_id,
                    vendor_location=Location(
                        latitude=o.vendor_location.latitude,
                        longitude=o.vendor_location.longitude,
                    ),
                    customer_location=Location(
                        latitude=o.customer_location.latitude,
                        longitude=o.customer_location.longitude,
                    ),
                    ready_time=o.ready_time,
                    preparation_time=o.preparation_time,
                    priority=o.priority,
                    demand=1,
                )
            )

        self.validate_riders(domain_riders)
        self.validate_orders(domain_orders)

        if algorithm.lower() == "nearest":
            solver = NearestNeighborSolver()
        else:
            solver = VRPSolver()

        return solver.solve(domain_orders, domain_riders)
