from dataclasses import dataclass, field


@dataclass(slots=True)
class RiderAssignment:
    rider_id: str
    order_ids: list[str]
    total_distance: int


@dataclass(slots=True)
class OptimizerStatistics:
    total_distance: int
    total_orders: int
    total_batches: int
    average_orders_per_rider: float
    solver_time: float


@dataclass(slots=True)
class OptimizerResult:
    assignments: list[RiderAssignment] = field(default_factory=list)
    statistics: OptimizerStatistics | None = None