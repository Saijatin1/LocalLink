# Hyperlocal Delivery Platform — v2 (Trimmed Architecture)

Target: Alwal / Secunderabad / Kompally, Hyderabad
5 services total. 3 boring, 2 genuinely novel.

---

## 1. Repo Structure

```
hyperlocal-platform/
├── services/
│   ├── auth-user-service/
│   ├── catalog-vendor-service/
│   ├── order-payment-service/
│   ├── delivery-service/
│   ├── conversational-agent/       # NEW — component A
│   └── batching-optimizer/         # NEW — component B
│
├── shared/
│   ├── models/          # shared Pydantic schemas
│   ├── auth/            # JWT helpers
│   ├── config/          # env loader
│   └── db/               # SQLAlchemy base
│
├── infra/
│   ├── docker-compose.yml   # postgres, redis, elasticsearch
│   └── nginx/                # API gateway config
│
├── scripts/
│   └── seed_data.py
│
└── docs/
    └── architecture.md
```

Each service is a standalone FastAPI app:
```
<service>/
├── app/
│   ├── main.py
│   ├── api/           # routers
│   ├── models/         # SQLAlchemy
│   ├── schemas/         # Pydantic
│   ├── services/         # business logic
│   └── core/              # config, db session
├── Dockerfile
└── requirements.txt
```

---

## 2. Component Context — the 3 core services (keep boring)

### 2.1 Auth/User Service
- Phone OTP login, JWT issuance, roles (`user`, `vendor`, `rider`)
- Addresses table with `lat`, `lng`, `area_tag` (`alwal | secunderabad | kompally`)
- `users_auth(id, phone, role, otp_hash, otp_expiry, is_verified)`
- `addresses(id, user_id, label, lat, lng, area_tag)`

### 2.2 Catalog/Vendor Service
- Vendor onboarding + product CRUD + stock, merged into one service
- `vendors(id, name, area_tag, lat, lng, is_active)`
- `products(id, vendor_id, name, price, stock_qty, category)`
- Stock decrement: `SELECT ... FOR UPDATE SKIP LOCKED` inside the order transaction — prevents overselling under concurrent orders
- Push updated stock/product to Elasticsearch on write (simple sync write-through is fine — don't build an outbox pattern for a project this size)

### 2.3 Order/Payment Service
- Cart (Redis, ephemeral, `cart:{user_id}` hash) + Order state machine + Razorpay/COD
- `orders(id, user_id, vendor_id, status, total_amount, address_id)`
- `order_items(order_id, product_id, qty, price_at_order)`
- States: `placed → confirmed → preparing → out_for_delivery → delivered` (+ `cancelled`)
- Order creation flow: reserve stock (Catalog service call) → confirm → trigger Delivery assignment

### 2.4 Delivery Service
- Rider registration (role=rider via Auth), nearest-available assignment, live location
- `riders(id, user_id, vehicle_type, is_available, current_lat, current_lng)`
- `deliveries(id, order_id, rider_id, assigned_at, delivered_at)`
- v1 assignment = simple radius/haversine query; gets replaced by the Batching Optimizer once orders queue up (see 3.2)

**None of the above need deep description in your paper — one architecture diagram + a paragraph each is enough. Your engineering effort goes into 3.1 and 3.2 below.**

---

## 3. Component Context — the 2 unique components

### 3.1 Conversational Ordering Agent

**What it does**: user chats naturally ("get stuff for maggi, something sweet too, budget 150") instead of browsing. Agent plans, calls tools against your real Catalog/Order services, asks clarifying questions when ambiguous, and never claims a product/price that isn't actually in your DB.

**Why it's the hard/interesting part**: grounding. An ungrounded LLM will happily say "added Maggi noodles for ₹14" when it's out of stock or doesn't exist. The whole engineering problem is forcing every claim the agent makes to come from a tool result, not from the model's own generation.

**Pipeline**:
1. User message → agent loop (ReAct-style: think → call tool → observe → repeat)
2. Tools exposed to the LLM (as function-calling schemas):
   - `search_products(query, vendor_area) -> [{id, name, price, stock}]`
   - `get_product(id) -> {..., stock}`
   - `add_to_cart(product_id, qty)`
   - `get_cart() -> current cart + running total`
   - `check_budget_constraint(cart, budget) -> ok / over_by`
3. Agent must call `search_products` before ever naming a product — never let it answer from memory
4. If a query is ambiguous ("something sweet") and multiple matches exist, agent asks a clarifying question instead of guessing (this is a state you explicitly design for, not left to the LLM's judgment — check candidate count and force a clarification turn if > N)
5. On confirmation, agent calls `add_to_cart` for each item, hands off to Order/Payment service checkout as normal

**Where it lives**: standalone FastAPI service, calls Catalog/Order services over HTTP just like a normal client would (not privileged internal access) — this is important for grounding integrity, the agent has no more authority than a real user.

**Suggested implementation**:
- Start with direct Anthropic API tool-calling (function-calling schema, multi-turn loop) — don't reach for a heavy agent framework (LangGraph etc.) until the basic loop is working; the loop itself is only ~50-100 lines
- Session/conversation state: Redis, keyed by `agent_session:{user_id}`, storing message history + current cart draft
- Log every tool call + result — this becomes your grounding/hallucination-rate metric later (did the agent ever reference a product_id that wasn't returned by a prior `search_products` call?)

**What to measure** (this is your paper's evaluation section for this component):
- Task success rate: % of conversations that reach a valid, checked-out cart within budget
- Hallucination rate: agent references a product/price not backed by a tool result (should be ~0% if grounding works — that near-zero number, achieved through this design, is your actual claim)
- Turns-to-completion (efficiency)
- Latency/cost per completed order vs. a traditional search-and-click flow

---

### 3.2 Delivery Batching Optimizer

**What it does**: when multiple orders are live across your 3 areas, decide which rider takes which order(s) to minimize total distance/time, instead of "nearest idle rider" naive assignment.

**Why it's interesting**: this is a real constraint-satisfaction/optimization problem, not ML-flavored guessing — clean to formulate, clean to evaluate, and completely different skillset from the agent (OR-Tools / combinatorial optimization vs. LLM tool-calling).

**Problem formulation** (this is effectively a small Vehicle Routing Problem with capacity + time windows):
- Inputs: set of pending orders (pickup = vendor location, dropoff = customer address, ready_time), set of available riders (current location, capacity — e.g. max 2-3 concurrent orders)
- Objective: minimize total travel distance/time across all riders, subject to: each order assigned to exactly one rider, rider capacity not exceeded, orders picked up after `ready_time`
- This is small-scale (tens of orders, single-digit riders per area at a time) — solvable with Google OR-Tools' CP-SAT or routing solver directly, no need for custom heuristics or ML

**Suggested implementation**:
- Standalone FastAPI service, triggered periodically (e.g. every 60-90s batching window) or on-demand when order queue crosses a threshold
- `POST /batch-assign` — pulls pending orders + available riders from Delivery service, runs OR-Tools solve, writes assignments back
- Use `ortools.constraint_solver.routing_enums_pb2` / `pywrapcp` — Google's routing library has this VRP formulation largely built in, you're mostly writing the distance matrix + constraints, not the solver
- Distance matrix: haversine for a first pass (good enough at this scale), can swap in a real routing API later if you want road-distance accuracy

**What to measure**:
- Average delivery time / total rider-distance: batching optimizer vs. naive nearest-idle-rider assignment, under simulated concurrent order load
- Solve time (must stay well under your batching window — if OR-Tools takes 45s to solve a 90s window, that's a real finding to report, not a bug to hide)
- Behavior as order volume scales (10 vs 50 vs 100 concurrent orders) — this gives you a nice scaling chart for the paper

---

## 4. Build Sequencing

1. **Weeks 1-4**: Auth/User → Catalog/Vendor → Order/Payment (happy path, COD only) → Delivery (naive nearest-rider assignment). Get a working vertical slice end to end.
2. **Weeks 5-10**: Conversational Agent — get the tool-calling loop working against your real Catalog/Order services, grounding checks, clarification handling.
3. **Weeks 11-15**: Batching Optimizer — formulate the VRP, wire up OR-Tools, replace naive assignment, build the load simulator you'll need for evaluation anyway.
4. **Weeks 16-20**: Evaluation for both components (hallucination rate + task success for the agent, distance/time savings for the optimizer), write-up, polish.

Razorpay integration, live rider tracking UI, and admin dashboards are nice-to-haves — build them only if time remains after the two core components are evaluated. The paper doesn't need them; the demo benefits from them but isn't worthless without.

---

## 5. Why This Is a Clean Systems Paper

- Two independently novel components, no overlapping skillset (LLM agentic grounding vs. classic combinatorial optimization) — shows breadth without redundant work
- Both have crisp, honest evaluation metrics you can actually produce yourself (no external benchmark dataset needed — you're measuring your own system's behavior under your own simulated load)
- Both are *useful*, not decorative — a real vendor/rider/customer benefits, which matters if you ever want to pitch this beyond the paper
- 3 supporting services stay deliberately boring — reviewers won't penalize plain CRUD, they'll penalize weak evaluation, so that's where your time should go instead
