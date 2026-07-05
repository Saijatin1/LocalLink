from app.models.order import Order
from app.models.rider import Rider
from app.solver.base_solver import BaseSolver
from app.solver.optimizer_result import (
    OptimizerResult,
    RiderAssignment,
)


class NearestNeighborSolver(BaseSolver):

    def solve(
        self,
        orders: list[Order],
        riders: list[Rider],
    ) -> OptimizerResult:

        assignments = []

        available = {
            rider.rider_id: rider.remaining_capacity
            for rider in riders
        }

        for order in orders:

            rider = max(
                available,
                key=available.get,
            )

            assignments.append(
                RiderAssignment(
                    rider_id=rider,
                    order_ids=[order.order_id],
                    total_distance=0,
                )
            )

            available[rider] -= 1

        return OptimizerResult(
            assignments=assignments
        )