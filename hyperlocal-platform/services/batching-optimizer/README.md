# Batching Optimizer Microservice

This microservice provides high-performance hyperlocal batching optimization algorithms using Google OR-Tools (Vehicle Routing Problems) and Nearest Neighbor heuristics.

## Architecture

```
app/
├── api/                  # Endpoints (batch-assign, simulate, metrics)
├── core/                 # Configuration and Logger configurations
├── db/                   # Database engine, Session & Base models
├── models/               # Order, Rider, RoutingNode domain models
├── repositories/         # Metrics Repository (SQLAlchemy 2)
├── schemas/              # Pydantic validation schemas
├── services/             # Batching, Simulation, Metrics business logic
├── solver/               # VRP solvers and helper utilities
└── utils/                # Global validation and helper modules
```

## Setup & Running Local

### System Requirements
* Python 3.12+ (or Docker)

### Installation
1. Clone this repository.
2. Initialize virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Copy environment settings and modify them if necessary:
   ```bash
   copy .env.example .env
   ```

### Running Server
```bash
uvicorn app.main:app --reload
```

## Running Docker
To start the FastAPI service along with PostgreSQL and Redis:
```bash
docker-compose up --build
```

## API Endpoints

### 1. Batch Assignment (`POST /batch/batch-assign`)
Main route optimization endpoint. Supports `algorithm=vrp` and `algorithm=nearest`.
* **URL Parameters:** `algorithm` (default: `vrp`)
* **Payload Format:**
  ```json
  {
    "orders": [...],
    "riders": [...]
  }
  ```

### 2. Simulation (`POST /simulation/simulate`)
Simulates order assignment based on a set number of randomly generated orders within areas like Alwal, Secunderabad, and Kompally.
* **Payload Format:**
  ```json
  {
    "num_orders": 25,
    "algorithm": "vrp"
  }
  ```

### 3. Consolidated Metrics (`GET /metrics`)
Returns summary statistics of historical optimization/simulation runs persisted to PostgreSQL.

## Benchmarks
To compare the execution performance and distances of Nearest Neighbor vs VRP solvers, run:
```bash
.venv\Scripts\python.exe scripts/benchmark.py
```
This produces a detailed summary table and writes output to `benchmark_results.csv`.
