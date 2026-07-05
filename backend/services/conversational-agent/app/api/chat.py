from fastapi import APIRouter, HTTPException

from app.agent.loop import run_agent
from app.agent.state import AgentState
from app.clients.cart_client import add_to_cart, get_cart
from app.clients.catalog_client import search_products, load_products
from app.clients.session_client import get_or_create_session, reset_session
from app.schemas.cart import Cart
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ResetSessionRequest,
    ResetSessionResponse,
)
from app.schemas.product import Product

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Process a natural language chat message and return the agent's response."""
    session = get_or_create_session(request.user_id)
    state = AgentState(session)
    return run_agent(state, request.message)


@router.post("/reset-session", response_model=ResetSessionResponse)
def reset_session_route(request: ResetSessionRequest) -> ResetSessionResponse:
    """Reset a user's session — clears history, cart draft, and tool log."""
    reset_session(request.user_id)
    return ResetSessionResponse(message=f"Session reset for user '{request.user_id}'.")


@router.get("/catalog", response_model=list[Product])
def catalog(
    query: str | None = None,
    vendor_area: str | None = None,
    max_price: float | None = None,
) -> list[Product]:
    """Browse/search the product catalog."""
    if query:
        return search_products(query=query, vendor_area=vendor_area, max_price=max_price)
    products = load_products()
    if vendor_area:
        products = [p for p in products if p.area_tag == vendor_area]
    if max_price is not None:
        products = [p for p in products if p.price <= max_price]
    return [p for p in products if p.stock_qty > 0]


@router.get("/cart/{user_id}", response_model=Cart)
def cart_get(user_id: str) -> Cart:
    """Get the current cart for a user."""
    return get_cart(user_id)


@router.post("/cart/add", response_model=Cart)
def cart_add(user_id: str, product_id: int, qty: int = 1) -> Cart:
    """Add a product to the cart directly (bypasses LLM)."""
    try:
        return add_to_cart(user_id, product_id, qty)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
