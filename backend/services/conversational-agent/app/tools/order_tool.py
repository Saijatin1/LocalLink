PLACE_ORDER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "place_order",
        "description": "Place an order for the current cart contents. (Not yet implemented — will hand off to Order service in Phase 1.)",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user's unique ID",
                },
                "delivery_area": {
                    "type": "string",
                    "description": "Delivery area tag for the order",
                },
            },
            "required": ["user_id"],
        },
    },
}

CHECKOUT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "checkout",
        "description": "Confirm the cart and proceed to payment/checkout. (Not yet implemented.)",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user's unique ID",
                },
            },
            "required": ["user_id"],
        },
    },
}


def execute_place_order(user_id: str, delivery_area: str | None = None) -> str:
    """Stub: return placeholder message. Will call Order service in Phase 1."""
    area_msg = f" for delivery area '{delivery_area}'" if delivery_area else ""
    return f"[Not yet implemented] Would place order for user {user_id}{area_msg} and hand off to Order service."


def execute_checkout(user_id: str) -> str:
    """Stub: return placeholder message."""
    return f"[Not yet implemented] Would initiate checkout for user {user_id}."
