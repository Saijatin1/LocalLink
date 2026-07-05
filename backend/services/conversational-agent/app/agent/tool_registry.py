from app.tools import catalog_tool, cart_tool, budget_tool, order_tool


def get_all_schemas() -> list[dict]:
    """Return the list of tool schemas in the format the LLM provider expects."""
    return [
        catalog_tool.SCHEMA,
        cart_tool.ADD_SCHEMA,
        cart_tool.VIEW_SCHEMA,
        budget_tool.SCHEMA,
        order_tool.PLACE_ORDER_SCHEMA,
        order_tool.CHECKOUT_SCHEMA,
    ]


def get_dispatch_map() -> dict[str, callable]:
    """
    Return a {tool_name: callable} dispatch map.

    Each callable takes **kwargs and returns a formatted string result.
    """
    return {
        "search_catalog": catalog_tool.execute,
        "add_to_cart": cart_tool.execute_add,
        "view_cart": cart_tool.execute_view,
        "check_budget": budget_tool.execute,
        "place_order": order_tool.execute_place_order,
        "checkout": order_tool.execute_checkout,
    }
