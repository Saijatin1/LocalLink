import json
import os
import re
from pathlib import Path

from app.schemas.product import Product


def load_products() -> list[Product]:
    """Load all products from catalog.json. Written as if body will be httpx.get(...)."""
    path = Path(os.path.dirname(__file__)) / ".." / "data" / "catalog.json"
    with open(path) as f:
        raw = json.load(f)
    return [Product(**item) for item in raw]


def search_products(
    query: str,
    vendor_area: str | None = None,
    min_gsm: int | None = None,
    min_rating: float | None = None,
    max_price: float | None = None,
) -> list[Product]:
    """
    Search products by name/description keyword, optionally filtering by area,
    fabric GSM (minimum), rating (minimum), and max price.

    Written as if the body will be replaced with httpx.get(...) later.
    """
    products = load_products()

    # Normalise query into lower-case tokens
    tokens = re.sub(r"[^a-z0-9\s]", "", query.lower()).split()
    # Exclude bare numeric tokens — they cause accidental matches against weights/sizes (e.g. "500" matches "500g")
    tokens = [t for t in tokens if not t.isdigit()]

    results: list[Product] = []
    for p in products:
        # Basic keyword match on name and category (normalised the same way)
        name_normalised = re.sub(r"[^a-z0-9\s]", "", p.name.lower())
        category_normalised = re.sub(r"[^a-z0-9\s]", "", p.category.lower())
        if not any(token in name_normalised or token in category_normalised for token in tokens):
            continue

        # Stock check
        if p.stock_qty <= 0:
            continue

        results.append(p)

    # Apply optional filters
    if vendor_area:
        results = [p for p in results if p.area_tag == vendor_area]
    if min_gsm is not None:
        results = [p for p in results if p.fabric_gsm is not None and p.fabric_gsm >= min_gsm]
    if min_rating is not None:
        results = [p for p in results if p.rating is not None and p.rating >= min_rating]
    if max_price is not None:
        results = [p for p in results if p.price <= max_price]

    return results


def get_product(product_id: int) -> Product | None:
    """Get a single product by ID. Written as if body will be httpx.get(...)."""
    products = load_products()
    return next((p for p in products if p.id == product_id), None)
