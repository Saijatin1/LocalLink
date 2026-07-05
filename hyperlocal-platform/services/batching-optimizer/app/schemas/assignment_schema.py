from pydantic import BaseModel


class AssignmentSchema(BaseModel):
    rider_id: str
    orders: list[str]


class StatisticsSchema(BaseModel):
    total_distance: float
    solver_time: float
    num_batches: int


class BatchAssignmentResponse(BaseModel):
    assignments: list[AssignmentSchema]
    statistics: StatisticsSchema