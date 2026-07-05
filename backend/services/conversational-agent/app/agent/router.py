from typing import Any

from app.schemas.cart import Cart
from app.schemas.product import Product
from app.agent.planner import check_ambiguity, check_empty_result, check_budget_gate


def get_instructions(
    search_candidates: list[Product],
    cart: Cart,
    ambiguity_threshold: int,
    budget: float | None = None,
) -> list[dict[str, str]] | None:
    """
    Given the planner's verdicts, decide what instruction to inject.

    Returns a list of system-style instruction dicts, or None if no gate fires.
    The instructions override the model's behaviour for the next turn.
    """
    instructions: list[dict[str, str]] = []

    # 1. Empty-result gate — fires before ambiguity
    if check_empty_result(search_candidates):
        instructions.append({
            "role": "user",
            "content": (
                "[SYSTEM: The product search returned no results for that specific query. "
                "Inform the user that the exact item isn't available, then search again "
                "with a broader or related keyword to find similar products that could work as alternatives. "
                "Only suggest products returned by your searches — never invent items.]"
            ),
        })
        return instructions

    # 2. Ambiguity gate
    if check_ambiguity(search_candidates, ambiguity_threshold):
        candidate_names = [f"  - {c.name} (₹{c.price})" for c in search_candidates]
        candidate_list = "\n".join(candidate_names)
        instructions.append({
            "role": "user",
            "content": (
                f"[SYSTEM: The search returned multiple possible items:\n{candidate_list}\n"
                "The result is ambiguous. You MUST ask the user which specific item(s) they want "
                "by listing the options above. Do NOT guess or pick on their behalf.]"
            ),
        })
        return instructions

    # 3. Budget gate
    if budget is not None:
        budget_result = check_budget_gate(cart, budget)
        if not budget_result["ok"]:
            instructions.append({
                "role": "user",
                "content": (
                    f"[SYSTEM: The cart total (₹{cart.total}) exceeds the user's budget (₹{budget}) "
                    f"by ₹{budget_result['over_by']}. "
                    "You MUST report this to the user and ask how they'd like to proceed "
                    "(e.g. remove items, increase budget, etc.).]"
                ),
            })
            return instructions

    # No gate fired
    return None
