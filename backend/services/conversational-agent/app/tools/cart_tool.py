from app.clients.cart_client import add_to_cart, get_cart
from app.schemas.cart import Cart


ADD_SCHEMA = {
    "type": "function",
    "function": {
        "name": "add_to_cart",
        "description": "Add a product to the user's cart by product ID and quantity.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user's unique ID",
                },
                "product_id": {
                    "type": "integer",
                    "description": "The product ID to add",
                },
                "qty": {
                    "type": "integer",
                    "description": "Quantity to add (default 1)",
                },
            },
            "required": ["user_id", "product_id"],
        },
    },
}

VIEW_SCHEMA = {
    "type": "function",
    "function": {
        "name": "view_cart",
        "description": "View the current contents of the user's cart.",
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


def execute_add(user_id: str, product_id: int, qty: int = 1) -> str:
    """Add a product to cart and return a formatted string."""
    try:
        cart = add_to_cart(user_id=user_id, product_id=product_id, qty=qty)
        return _format_cart(cart)
    except ValueError as e:
        return str(e)


def execute_view(user_id: str) -> str:
    """View cart contents and return a formatted string."""
    cart = get_cart(user_id=user_id)
    return _format_cart(cart)


def _format_cart(cart: Cart) -> str:
    if not cart.items:
        return "Cart is empty."
    lines = [f"Cart for user {cart.user_id}:"]
    for item in cart.items:
        lines.append(f"  - {item.name} (x{item.qty}) — ₹{item.price} each = ₹{item.price * item.qty}")
    lines.append(f"Total: ₹{cart.total}")
    return "\n".join(lines)
