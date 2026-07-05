from datetime import datetime

from app.models.order import Location
from app.models.order import Order
from app.models.rider import Rider

from app.solver.vrp_solver import VRPSolver


orders = [
    Order(
        "O1",
        Location(17.45,78.39),
        Location(17.46,78.41),
        datetime.now(),
        10,
    ),
    Order(
        "O2",
        Location(17.47,78.40),
        Location(17.48,78.43),
        datetime.now(),
        5,
    )
]

riders = [
    Rider(
        "R1",
        Location(17.44,78.38),
        3,
        0,
    )
]

solver = VRPSolver()

solver.solve(
    orders,
    riders,
)

print("Solver Initialized Successfully")