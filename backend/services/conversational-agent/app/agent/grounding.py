import json
import re
from typing import Any

from loguru import logger

from app.schemas.product import Product


def _extract_numeric_prices(text: str) -> list[float]:
    """Extract price-like numbers from text (₹ followed by number, or just number near '₹')."""
    prices = []
    # Match ₹1234.56 or ₹1234 or Rs. 1234
    for match in re.finditer(r"[₹Rs.]+\s*(\d+(?:\.\d+)?)", text):
        prices.append(float(match.group(1)))
    return prices


def _extract_product_names(text: str) -> list[str]:
    """
    Extract potential product names mentioned in the text.
    Uses heuristics: looks for capitalized words/phrases that look like product names.
    """
    # Look for quoted strings (likely product names)
    quoted = re.findall(r'"([^"]+)"', text)
    return quoted


def _get_known_products(tool_log: list[dict]) -> list[dict]:
    """
    Extract all products that appeared in tool results from the session log.
    Returns list of dicts with name, price, id.
    """
    known = []
    for entry in tool_log:
        if entry.get("type") == "tool_result" and entry.get("tool_name") == "search_catalog":
            result_text = entry.get("result", "")
            # Parse product lines from result
            # Format: "  - [1] Maggi Noodles — ₹14.0 [alwal, stock: 100]"
            for line in result_text.split("\n"):
                match = re.match(r"\s*-\s*\[(\d+)\]\s*(.+?)\s*[—–-]\s*[₹Rs.]*([\d.]+)", line)
                if match:
                    known.append({
                        "id": int(match.group(1)),
                        "name": match.group(2).strip(),
                        "price": float(match.group(3)),
                    })
    return known


def _get_known_ids(tool_log: list[dict]) -> set[int]:
    """Extract all product IDs that were added to cart."""
    ids = set()
    for entry in tool_log:
        if entry.get("type") == "tool_result" and entry.get("tool_name") == "add_to_cart":
            args = entry.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    continue
            pid = args.get("product_id")
            if pid is not None:
                ids.add(int(pid))
    return ids


def check_grounding(text: str, tool_log: list[dict]) -> dict:
    """
    Check whether every claim in the final response is grounded in tool results.

    Returns {"flagged": bool, "details": list[str]}.
    """
    details: list[str] = []
    known_products = _get_known_products(tool_log)
    known_ids = _get_known_ids(tool_log)

    # Build lookup maps
    known_names = {p["name"].lower(): p for p in known_products}
    known_prices = {p["price"] for p in known_products}

    # Check quoted product names
    mentioned_names = _extract_product_names(text)
    for name in mentioned_names:
        name_lower = name.lower()
        if name_lower not in known_names:
            details.append(f"Product '{name}' not found in any tool result")

    # Check prices mentioned in context of products
    mentioned_prices = _extract_numeric_prices(text)
    for price in mentioned_prices:
        # Allow price if it matches a known product price (within 0.01 tolerance)
        if not any(abs(price - kp) < 0.01 for kp in known_prices):
            details.append(f"Price ₹{price} not found in any tool result")

    flagged = len(details) > 0
    if flagged:
        logger.warning(f"Grounding check flagged: {details}")

    return {"flagged": flagged, "details": details}
