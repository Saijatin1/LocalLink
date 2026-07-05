from app.models.order import Location
from app.utils.haversine import haversine_distance


def distance_between(
    source: Location,
    destination: Location,
) -> int:
    return haversine_distance(
        source.latitude,
        source.longitude,
        destination.latitude,
        destination.longitude,
    )