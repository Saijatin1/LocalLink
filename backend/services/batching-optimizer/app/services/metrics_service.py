from app.solver.optimizer_result import OptimizerResult

class MetricsService:

    @staticmethod
    def compute_metrics(
        result: OptimizerResult,
        solver_time: float,
        num_riders_total: int,
    ) -> dict:
        total_distance = 0
        total_orders = 0
        num_batches = len(result.assignments)
        
        assigned_riders = set()
        for assignment in result.assignments:
            total_distance += assignment.total_distance
            total_orders += len(assignment.order_ids)
            assigned_riders.add(assignment.rider_id)

        avg_distance = total_distance / max(1, total_orders)
        # Assuming average speed is 30 km/h (8.33 m/s) + 5 mins service time per order
        # Distance is in meters
        avg_time = (total_distance / 8.33) / max(1, total_orders) + (total_orders * 300 / max(1, total_orders))
        
        rider_utilization = len(assigned_riders) / max(1, num_riders_total)
        avg_batch_size = total_orders / max(1, num_batches)
        
        # Estimate fuel savings: VRP base vs single delivery routes
        # Assumes individual deliveries without batching would travel twice the distance between vendor-customer.
        # Let's say batching saves ~25% distance on average compared to un-batched.
        fuel_savings_liters = (total_distance * 0.05 / 1000) * 0.25  # 0.05 liters per km, 25% savings

        return {
            "total_distance": total_distance,
            "total_orders": total_orders,
            "num_batches": num_batches,
            "average_delivery_distance": avg_distance,
            "average_delivery_time": avg_time,
            "average_rider_utilization": rider_utilization,
            "average_batch_size": avg_batch_size,
            "fuel_savings_estimate_liters": fuel_savings_liters,
            "solver_execution_time_seconds": solver_time,
        }

    def compare_algorithms(
        self,
        nn_result: OptimizerResult,
        nn_time: float,
        vrp_result: OptimizerResult,
        vrp_time: float,
        num_riders_total: int,
    ) -> dict:
        nn_metrics = self.compute_metrics(nn_result, nn_time, num_riders_total)
        vrp_metrics = self.compute_metrics(vrp_result, vrp_time, num_riders_total)
        return {
            "nearest_neighbor": nn_metrics,
            "vrp": vrp_metrics,
        }
