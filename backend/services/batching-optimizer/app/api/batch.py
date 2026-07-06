from fastapi import APIRouter, Query, Depends
from app.schemas.batch_request import BatchRequest
from app.schemas.assignment_schema import BatchAssignmentResponse, AssignmentSchema, StatisticsSchema
from app.services.batch_service import BatchService

router = APIRouter(prefix="/batch", tags=["batch"])

@router.post("/batch-assign", response_model=BatchAssignmentResponse)
def batch_assign(
    request: BatchRequest,
    algorithm: str = Query("vrp", regex="^(vrp|nearest)$"),
    batch_service: BatchService = Depends(),
):
    result = batch_service.run_optimization(request, algorithm=algorithm)
    
    assignments = [
        AssignmentSchema(
            rider_id=a.rider_id,
            orders=a.order_ids
        )
        for a in result.assignments
    ]
    
    # Calculate stats if not present
    if result.statistics:
        stats = StatisticsSchema(
            total_distance=float(result.statistics.total_distance),
            solver_time=float(result.statistics.solver_time),
            num_batches=int(result.statistics.total_batches)
        )
    else:
        stats = StatisticsSchema(
            total_distance=float(sum(a.total_distance for a in result.assignments)),
            solver_time=0.0,
            num_batches=len(assignments)
        )
        
    return BatchAssignmentResponse(
        assignments=assignments,
        statistics=stats
    )
