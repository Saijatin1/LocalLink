from sqlalchemy.orm import Session
from app.db.base import SolverMetricModel

class MetricsRepository:

    def __init__(self, db: Session):
        self.db = db

    def save_metric(self, model: SolverMetricModel) -> SolverMetricModel:
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def get_all_metrics(self, limit: int = 100) -> list[SolverMetricModel]:
        return self.db.query(SolverMetricModel).order_by(SolverMetricModel.timestamp.desc()).limit(limit).all()

    def get_summary(self) -> dict:
        # Compute basic aggregations from history
        records = self.db.query(SolverMetricModel).all()
        if not records:
            return {
                "total_simulation_runs": 0,
                "average_delivery_distance": 0.0,
                "average_delivery_time": 0.0,
                "average_rider_utilization": 0.0,
                "average_batch_size": 0.0,
                "total_fuel_saved_liters": 0.0,
                "average_solver_time": 0.0,
            }
        
        total_runs = len(records)
        avg_dist = sum(r.average_delivery_distance for r in records) / total_runs
        avg_time = sum(r.average_delivery_time for r in records) / total_runs
        avg_util = sum(r.average_rider_utilization for r in records) / total_runs
        avg_batch = sum(r.average_batch_size for r in records) / total_runs
        total_fuel = sum(r.fuel_savings_liters for r in records)
        avg_solve_time = sum(r.solver_time_seconds for r in records) / total_runs

        return {
            "total_simulation_runs": total_runs,
            "average_delivery_distance": avg_dist,
            "average_delivery_time": avg_time,
            "average_rider_utilization": avg_util,
            "average_batch_size": avg_batch,
            "total_fuel_saved_liters": total_fuel,
            "average_solver_time": avg_solve_time,
        }
