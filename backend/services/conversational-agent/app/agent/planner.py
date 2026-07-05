from app.schemas.cart import Cart
from app.clients.cart_client import check_budget as _check_budget
from app.schemas.product import Product


def check_ambiguity(candidates: list[Product], threshold: int) -> bool:
    """
    Check if the number of candidate products exceeds the ambiguity threshold.
    Returns True if the result is ambiguous and needs a clarifying question.
    """
    return len(candidates) > threshold


def check_empty_result(candidates: list[Product]) -> bool:
    """Check if the search returned no results."""
    return len(candidates) == 0


def check_budget_gate(cart: Cart, budget: float) -> dict:
    """
    Check if the cart total exceeds the user's budget.
    Returns {"ok": True} or {"ok": False, "over_by": float}.
    Delegates to the cart client so arithmetic is always real.
    """
    return _check_budget(cart, budget)
