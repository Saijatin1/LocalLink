from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class SolverMetricModel(Base):
    __tablename__ = "solver_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    algorithm = Column(String(50), nullable=False)
    total_orders = Column(Integer, nullable=False)
    total_batches = Column(Integer, nullable=False)
    total_distance_meters = Column(Float, nullable=False)
    solver_time_seconds = Column(Float, nullable=False)
    average_delivery_distance = Column(Float, nullable=False)
    average_delivery_time = Column(Float, nullable=False)
    average_rider_utilization = Column(Float, nullable=False)
    average_batch_size = Column(Float, nullable=False)
    fuel_savings_liters = Column(Float, nullable=False)
    extra_data = Column(JSON, nullable=True)
