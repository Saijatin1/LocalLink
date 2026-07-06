from abc import ABC
from abc import abstractmethod

from app.models.order import Order
from app.models.rider import Rider
from app.solver.optimizer_result import OptimizerResult


class BaseSolver(ABC):

    @abstractmethod
    def solve(
        self,
        orders: list[Order],
        riders: list[Rider],
    ) -> OptimizerResult:
        ...