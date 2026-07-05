from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_batch_assign_empty():
    # Empty orders/riders fails our BatchService validation inside the logic (raises ValueError, which maps to 400 via exception handler or custom logic).
    response = client.post("/batch/batch-assign", json={"orders": [], "riders": []})
    assert response.status_code == 400


def test_batch_assign_valid():
    payload = {
        "orders": [
            {
                "order_id": "ord_1",
                "vendor_location": {"latitude": 17.5021, "longitude": 78.5042},
                "customer_location": {"latitude": 17.5045, "longitude": 78.5065},
                "ready_time": "2026-07-05T17:00:00Z",
                "preparation_time": 10,
                "priority": 1
            }
        ],
        "riders": [
            {
                "rider_id": "rider_1",
                "current_location": {"latitude": 17.5010, "longitude": 78.5020},
                "capacity": 3,
                "current_load": 0,
                "available": True
            }
        ]
    }
    response = client.post("/batch/batch-assign?algorithm=vrp", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "assignments" in data
    assert "statistics" in data

def test_simulation_api():
    response = client.post("/simulation/simulate", json={"num_orders": 10, "algorithm": "nearest"})
    assert response.status_code == 200
    data = response.json()
    assert data["algorithm"] == "nearest"
    assert "metrics" in data
    assert "assignments" in data

def test_metrics_api():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "recent_runs" in data
