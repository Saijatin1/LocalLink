from app.models.order import Order
from app.models.rider import Rider

def validate_input_data(orders: list[Order], riders: list[Rider]) -> None:
    if not orders:
        raise ValueError("Order list cannot be empty.")
    if not riders:
        raise ValueError("Rider list cannot be empty.")
    
    for order in orders:
        if not order.order_id:
            raise ValueError("Order must have a valid order_id.")
        if order.preparation_time < 0:
            raise ValueError("Order preparation time cannot be negative.")
        if not (-90 <= order.vendor_location.latitude <= 90) or not (-180 <= order.vendor_location.longitude <= 180):
            raise ValueError(f"Invalid vendor location for order {order.order_id}.")
        if not (-90 <= order.customer_location.latitude <= 90) or not (-180 <= order.customer_location.longitude <= 180):
            raise ValueError(f"Invalid customer location for order {order.order_id}.")

    for rider in riders:
        if not rider.rider_id:
            raise ValueError("Rider must have a valid rider_id.")
        if rider.capacity <= 0:
            raise ValueError("Rider capacity must be positive.")
        if not (-90 <= rider.current_location.latitude <= 90) or not (-180 <= rider.current_location.longitude <= 180):
            raise ValueError(f"Invalid current location for rider {rider.rider_id}.")
