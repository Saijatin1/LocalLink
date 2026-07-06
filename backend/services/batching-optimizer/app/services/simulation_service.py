import random
from datetime import datetime, timedelta
from app.models.order import Order, Location
from app.models.rider import Rider

# Center coordinates for regions in Hyderabad
LOCATIONS = {
    "Alwal": {"latitude": 17.5021, "longitude": 78.5042},
    "Secunderabad": {"latitude": 17.4399, "longitude": 78.5020},
    "Kompally": {"latitude": 17.5385, "longitude": 78.4728},
}

class SimulationService:

    @staticmethod
    def _generate_random_location(center_name: str) -> Location:
        center = LOCATIONS[center_name]
        # Offset coordinates by a small random value (approx 1-5 km)
        lat_offset = random.uniform(-0.02, 0.02)
        lon_offset = random.uniform(-0.02, 0.02)
        return Location(
            latitude=center["latitude"] + lat_offset,
            longitude=center["longitude"] + lon_offset,
        )

    def generate_orders(self, count: int) -> list[Order]:
        orders = []
        regions = list(LOCATIONS.keys())
        for i in range(count):
            region = random.choice(regions)
            vendor_loc = self._generate_random_location(region)
            customer_loc = self._generate_random_location(region)
            ready_time = datetime.now() + timedelta(minutes=random.randint(0, 30))
            prep_time = random.randint(5, 25)
            priority = random.randint(1, 5)
            
            orders.append(
                Order(
                    order_id=f"ord_{i+1}",
                    vendor_location=vendor_loc,
                    customer_location=customer_loc,
                    ready_time=ready_time,
                    preparation_time=prep_time,
                    priority=priority,
                    demand=1,
                )
            )
        return orders

    def generate_riders(self, count: int) -> list[Rider]:
        riders = []
        regions = list(LOCATIONS.keys())
        for i in range(count):
            region = random.choice(regions)
            loc = self._generate_random_location(region)
            capacity = random.randint(2, 5)
            riders.append(
                Rider(
                    rider_id=f"rider_{i+1}",
                    current_location=loc,
                    capacity=capacity,
                    current_load=0,
                    available=True,
                )
            )
        return riders
