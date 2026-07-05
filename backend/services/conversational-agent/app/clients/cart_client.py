from app.clients.catalog_client import get_product
from app.schemas.cart import Cart, CartItem


_carts: dict[str, Cart] = {}


def add_to_cart(user_id: str, product_id: int, qty: int) -> Cart:
    """Add a product to the user's cart. Written as if body will be httpx.post(...)."""
    product = get_product(product_id)
    if product is None:
        raise ValueError(f"Product {product_id} not found")
    if product.stock_qty <= 0:
        raise ValueError(f"Product {product.name} is out of stock")

    if user_id not in _carts:
        _carts[user_id] = Cart(user_id=user_id)

    cart = _carts[user_id]

    # Check if item already exists in cart
    for item in cart.items:
        if item.product_id == product_id:
            item.qty += qty
            break
    else:
        cart.items.append(CartItem(
            product_id=product_id,
            name=product.name,
            price=product.price,
            qty=qty,
        ))

    # Recalculate total
    cart.total = sum(item.price * item.qty for item in cart.items)
    return cart


def get_cart(user_id: str) -> Cart:
    """Get the user's current cart. Written as if body will be httpx.get(...)."""
    return _carts.get(user_id, Cart(user_id=user_id))


def check_budget(cart: Cart, budget: float) -> dict:
    """
    Check if the cart total is within budget.
    Returns {"ok": True} or {"ok": False, "over_by": float}.

    This does real arithmetic — never trust the LLM's own math for this.
    """
    if cart.total <= budget:
        return {"ok": True, "over_by": 0.0}
    return {"ok": False, "over_by": round(cart.total - budget, 2)}
