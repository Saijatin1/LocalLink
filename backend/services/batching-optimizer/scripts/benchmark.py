import csv
import time
import os
from tabulate import tabulate
from app.services.simulation_service import SimulationService
from app.services.batch_service import BatchService
from app.schemas.batch_request import BatchRequest
from app.schemas.order_schema import OrderSchema, LocationSchema
from app.schemas.rider_schema import RiderSchema

def run_benchmarks():
    print("Initializing benchmark suite...")
    simulation_service = SimulationService()
    batch_service = BatchService()
    
    sizes = [10, 25, 50, 100, 250, 500]
    results = []

    for size in sizes:
        print(f"Running benchmarks for size {size} orders...")
        orders = simulation_service.generate_orders(size)
        num_riders = max(2, size // 3)
        riders = simulation_service.generate_riders(num_riders)

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

        # Nearest Neighbor Benchmark
        start_nn = time.perf_counter()
        try:
            res_nn = batch_service.run_optimization(batch_request, algorithm="nearest")
            nn_time = time.perf_counter() - start_nn
            nn_dist = sum(a.total_distance for a in res_nn.assignments)
            nn_batches = len(res_nn.assignments)
        except Exception as e:
            nn_time = -1.0
            nn_dist = -1
            nn_batches = -1

        # VRP (OR-Tools) Benchmark
        start_vrp = time.perf_counter()
        try:
            res_vrp = batch_service.run_optimization(batch_request, algorithm="vrp")
            vrp_time = time.perf_counter() - start_vrp
            vrp_dist = res_vrp.statistics.total_distance if res_vrp.statistics else sum(a.total_distance for a in res_vrp.assignments)
            vrp_batches = res_vrp.statistics.total_batches if res_vrp.statistics else len(res_vrp.assignments)
        except Exception as e:
            vrp_time = -1.0
            vrp_dist = -1
            vrp_batches = -1

        results.append({
            "size": size,
            "riders": num_riders,
            "nn_time_s": nn_time,
            "nn_dist_m": nn_dist,
            "nn_batches": nn_batches,
            "vrp_time_s": vrp_time,
            "vrp_dist_m": vrp_dist,
            "vrp_batches": vrp_batches,
        })

    # Save to CSV
    csv_file = "benchmark_results.csv"
    with open(csv_file, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    # Print Table
    table_data = []
    for r in results:
        table_data.append([
            r["size"],
            r["riders"],
            f"{r['nn_time_s']:.4f}s" if r["nn_time_s"] >= 0 else "Error",
            f"{r['nn_dist_m']}m" if r["nn_dist_m"] >= 0 else "Error",
            r["nn_batches"],
            f"{r['vrp_time_s']:.4f}s" if r["vrp_time_s"] >= 0 else "Error",
            f"{r['vrp_dist_m']}m" if r["vrp_dist_m"] >= 0 else "Error",
            r["vrp_batches"],
        ])

    headers = ["Orders", "Riders", "NN Time", "NN Distance", "NN Batches", "VRP Time", "VRP Distance", "VRP Batches"]
    print("\nPerformance Summary Table:")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"\nCSV results written to {csv_file}")

if __name__ == "__main__":
    run_benchmarks()
