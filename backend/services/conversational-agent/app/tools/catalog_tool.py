from app.clients.catalog_client import search_products
from app.schemas.product import Product


SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_catalog",
        "description": "Search the product catalog by keyword (English only — translate any local-language product names to English first), optionally filtering by vendor area, minimum fabric GSM, minimum rating, and max price. Only pass non-null values for filters you actually need. Examples: doodh/milk/paalu → milk, anda → eggs, tamatar → tomato, aloo → potato, pyaaz → onion.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword(s) — e.g. 'maggi', 'chocolate', 'sweater'",
                },
                "vendor_area": {
                    "type": ["string", "null"],
                    "description": "Optional area to filter by (alwal, secunderabad, kompally). Pass null if not needed.",
                },
                "min_gsm": {
                    "type": ["integer", "null"],
                    "description": "Optional minimum fabric GSM for clothing items. Pass null if not needed.",
                },
                "min_rating": {
                    "type": ["number", "null"],
                    "description": "Optional minimum product rating (0.0-5.0). Pass null if not needed.",
                },
                "max_price": {
                    "type": ["number", "null"],
                    "description": "Optional maximum price filter in rupees. Pass null if not needed.",
                },
            },
            "required": ["query"],
        },
    },
}


def execute(query: str, vendor_area: str | None = None, min_gsm: int | None = None, min_rating: float | None = None, max_price: float | None = None) -> str:
    """Execute a catalog search and return a formatted string result."""
    # Normalise: treat falsy values as "not provided" in case the model passes 0 or ""
    if vendor_area is not None and not vendor_area:
        vendor_area = None
    if min_gsm is not None and min_gsm <= 0:
        min_gsm = None
    if min_rating is not None and min_rating <= 0:
        min_rating = None
    if max_price is not None and max_price <= 0:
        max_price = None

    results = search_products(
        query=query,
        vendor_area=vendor_area,
        min_gsm=min_gsm,
        min_rating=min_rating,
        max_price=max_price,
    )
    if not results:
        return "No products found matching the query."

    lines = [f"Found {len(results)} product(s):"]
    for p in results:
        attrs = []
        if p.fabric_gsm:
            attrs.append(f"fabric_gsm={p.fabric_gsm}")
        if p.material:
            attrs.append(f"material={p.material}")
        if p.rating:
            attrs.append(f"rating={p.rating}")

        attr_str = f" ({', '.join(attrs)})" if attrs else ""
        lines.append(f"  - [{p.id}] {p.name} — ₹{p.price}{attr_str} [{p.category}, {p.area_tag}, stock: {p.stock_qty}]")

    return "\n".join(lines)
