from app.models.order import Order
from app.models.rider import Rider
from app.solver.base_solver import BaseSolver
from app.solver.optimizer_result import OptimizerResult


class OptimizerService:

    def __init__(
        self,
        solver: BaseSolver,
    ):
        self.solver = solver

    def optimize(
        self,
        orders: list[Order],
        riders: list[Rider],
    ) -> OptimizerResult:
        return self.solver.solve(
            orders,
            riders,
        )
