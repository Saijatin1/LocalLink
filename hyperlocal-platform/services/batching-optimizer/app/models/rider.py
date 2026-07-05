from dataclasses import dataclass

from app.models.order import Location


@dataclass(slots=True)
class Rider:
    rider_id: str

    current_location: Location

    capacity: int

    current_load: int = 0

    available: bool = True

    @property
    def remaining_capacity(self) -> int:
        return self.capacity - self.current_load