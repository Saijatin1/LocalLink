from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.repositories.metrics_repository import MetricsRepository

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("")
def get_metrics(db: Session = Depends(get_db)):
    repo = MetricsRepository(db)
    summary = repo.get_summary()
    all_runs = repo.get_all_metrics(limit=10)
    
    return {
        "summary": summary,
        "recent_runs": [
            {
                "id": r.id,
                "timestamp": r.timestamp,
                "algorithm": r.algorithm,
                "total_orders": r.total_orders,
                "total_batches": r.total_batches,
                "total_distance_meters": r.total_distance_meters,
                "solver_time_seconds": r.solver_time_seconds,
                "average_delivery_distance": r.average_delivery_distance,
                "average_delivery_time": r.average_delivery_time,
                "average_rider_utilization": r.average_rider_utilization,
                "average_batch_size": r.average_batch_size,
                "fuel_savings_liters": r.fuel_savings_liters,
            }
            for r in all_runs
        ]
    }
