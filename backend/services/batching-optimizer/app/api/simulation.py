import time
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.base import SolverMetricModel
from app.repositories.metrics_repository import MetricsRepository
from app.services.simulation_service import SimulationService
from app.services.batch_service import BatchService
from app.services.metrics_service import MetricsService
from app.schemas.batch_request import BatchRequest
from app.schemas.order_schema import OrderSchema, LocationSchema
from app.schemas.rider_schema import RiderSchema

router = APIRouter(prefix="/simulation", tags=["simulation"])

class SimulationRequest(BaseModel):
    num_orders: int = Query(..., description="Number of orders to simulate: 10, 25, 50, 100, 250, 500")
    algorithm: str = Query("vrp", regex="^(vrp|nearest)$")

@router.post("/simulate")
def simulate(
    request_data: SimulationRequest,
    simulation_service: SimulationService = Depends(),
    batch_service: BatchService = Depends(),
    metrics_service: MetricsService = Depends(),
    db: Session = Depends(get_db),
):
    orders = simulation_service.generate_orders(request_data.num_orders)
    # Generate riders relative to the order load (approx 1 rider per 3 orders, min 2 riders)
    num_riders = max(2, request_data.num_orders // 3)
    riders = simulation_service.generate_riders(num_riders)

    # Convert generated domain models to schemas to feed to BatchService
    order_schemas = [
        OrderSchema(
            order_id=o.order_id,
            vendor_location=LocationSchema(latitude=o.vendor_location.latitude, longitude=o.vendor_location.longitude),
            customer_location=LocationSchema(latitude=o.customer_location.latitude, longitude=o.customer_location.longitude),
            ready_time=o.ready_time,
            preparation_time=o.preparation_time,
            priority=o.priority,
        )
        for o in orders
    ]

    rider_schemas = [
        RiderSchema(
            rider_id=r.rider_id,
            current_location=LocationSchema(latitude=r.current_location.latitude, longitude=r.current_location.longitude),
            capacity=r.capacity,
            current_load=r.current_load,
            available=r.available,
        )
        for r in riders
    ]

    batch_request = BatchRequest(orders=order_schemas, riders=rider_schemas)

    start_time = time.perf_counter()
    result = batch_service.run_optimization(batch_request, algorithm=request_data.algorithm)
    execution_time = time.perf_counter() - start_time

    metrics = metrics_service.compute_metrics(result, execution_time, len(riders))

    # Persist the metric to DB
    repo = MetricsRepository(db)
    metric_record = SolverMetricModel(
        algorithm=request_data.algorithm,
        total_orders=metrics["total_orders"],
        total_batches=metrics["num_batches"],
        total_distance_meters=metrics["total_distance"],
        solver_time_seconds=metrics["solver_execution_time_seconds"],
        average_delivery_distance=metrics["average_delivery_distance"],
        average_delivery_time=metrics["average_delivery_time"],
        average_rider_utilization=metrics["average_rider_utilization"],
        average_batch_size=metrics["average_batch_size"],
        fuel_savings_liters=metrics["fuel_savings_estimate_liters"],
    )
    repo.save_metric(metric_record)

    return {
        "algorithm": request_data.algorithm,
        "metrics": metrics,
        "assignments": [
            {"rider_id": a.rider_id, "orders": a.order_ids, "distance_m": a.total_distance}
            for a in result.assignments
        ]
    }
