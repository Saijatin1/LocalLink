from app.clients.cart_client import check_budget, get_cart


SCHEMA = {
    "type": "function",
    "function": {
        "name": "check_budget",
        "description": "Check if the current cart total is within the user's budget. Uses arithmetic, not LLM estimation.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user's unique ID",
                },
                "budget": {
                    "type": "number",
                    "description": "The user's budget amount in rupees",
                },
            },
            "required": ["user_id", "budget"],
        },
    },
}


def execute(user_id: str, budget: float) -> str:
    """Check budget and return a formatted result."""
    cart = get_cart(user_id=user_id)
    result = check_budget(cart, budget)
    if result["ok"]:
        return f"✅ Cart total ₹{cart.total} is within budget of ₹{budget}."
    else:
        return f"❌ Cart total ₹{cart.total} exceeds budget of ₹{budget} by ₹{result['over_by']}."
