from datetime import datetime

from app.models.order import Location, Order
from app.models.rider import Rider


def test_models():
    vendor = Location(
        latitude=17.512,
        longitude=78.489
    )

    customer = Location(
        latitude=17.523,
        longitude=78.495
    )

    order = Order(
        order_id="O1",
        vendor_location=vendor,
        customer_location=customer,
        ready_time=datetime.now(),
        preparation_time=10,
        priority=1,
    )

    rider = Rider(
        rider_id="R1",
        current_location=vendor,
        capacity=3,
        current_load=1,
    )

    print(order)
    print(rider)
    print(rider.remaining_capacity)


if __name__ == "__main__":
    test_models()