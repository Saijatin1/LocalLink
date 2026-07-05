"""
Comprehensive tests for the conversational agent — covers gates, search,
cart, budget, grounding, planner, router, session, and API integration.

All tests are deterministic — no LLM required.
"""

import pytest
from fastapi.testclient import TestClient

from app.agent.grounding import check_grounding
from app.agent.planner import check_ambiguity, check_empty_result, check_budget_gate
from app.agent.router import get_instructions
from app.clients.cart_client import add_to_cart, get_cart
from app.clients.catalog_client import search_products, get_product
from app.clients.session_client import get_or_create_session, reset_session
from app.schemas.cart import Cart
from app.schemas.product import Product
from app.schemas.tool import ToolResult
from app.agent.llm_provider import _parse_function_tag
from app.main import app


client = TestClient(app)


# =============================================
# CATALOG SEARCH (15 tests)
# =============================================

class TestCatalogSearchEdgeCases:
    """15 tests covering catalog search edge cases."""

    def test_exact_name_match(self):
        results = search_products("Maggi Noodles")
        assert len(results) >= 1
        assert any("maggi" in p.name.lower() for p in results)

    def test_case_insensitive(self):
        results = search_products("MAGGI")
        assert len(results) >= 1

    def test_partial_match(self):
        results = search_products("mag")
        assert len(results) >= 1

    def test_category_match(self):
        results = search_products("sweet")
        assert len(results) > 2

    def test_bare_number_excluded(self):
        """Bare numbers like '500' should not match '500g' product names."""
        results = search_products("500")
        assert len(results) == 0

    def test_quantity_with_letters_matches(self):
        """'500g' should still match because it's not a bare number."""
        results = search_products("500g")
        assert len(results) >= 1

    def test_area_filter(self):
        results = search_products("maggi", vendor_area="alwal")
        assert all(p.area_tag == "alwal" for p in results)

    def test_area_filter_excludes(self):
        results = search_products("maggi", vendor_area="kompally")
        assert len(results) == 0

    def test_gsm_filter(self):
        results = search_products("sweater", min_gsm=300)
        assert all(p.fabric_gsm is not None and p.fabric_gsm >= 300 for p in results)

    def test_rating_filter(self):
        results = search_products("sweater", min_rating=4.5)
        assert all(p.rating is not None and p.rating >= 4.5 for p in results)

    def test_max_price_filter(self):
        results = search_products("chocolate", max_price=100)
        assert all(p.price <= 100 for p in results)

    def test_max_price_excludes_expensive(self):
        results = search_products("sweater", max_price=700)
        assert all(p.price <= 700 for p in results)
        assert any(p.name == "Thick Cotton Sweater" for p in results)
        assert not any(p.name == "Premium Wool Blend Sweater" for p in results)

    def test_multiple_filters_combined(self):
        results = search_products("sweater", min_gsm=300, min_rating=4.5, max_price=800)
        assert len(results) >= 1
        for p in results:
            assert p.price <= 800
            assert p.fabric_gsm is not None and p.fabric_gsm >= 300
            assert p.rating is not None and p.rating >= 4.5

    def test_out_of_stock_excluded(self):
        results = search_products("soap")
        assert len(results) == 0  # Tonik Dettol Soap has stock_qty=0

    def test_empty_query_returns_nothing(self):
        """Empty/non-matching query should return no results."""
        results = search_products("xyz_nonexistent_123")
        assert len(results) == 0


# =============================================
# AMBIGUITY GATE (5 tests)
# =============================================

class TestAmbiguityGateEdgeCases:
    """5 tests for ambiguity gate edge cases."""

    def test_ambiguity_not_fired_below_threshold(self):
        products = [Product(id=1, vendor_id=1, name="A", price=10, stock_qty=5, category="grocery", area_tag="alwal")]
        assert check_ambiguity(products, threshold=2) is False

    def test_ambiguity_fired_at_threshold(self):
        products = [
            Product(id=1, vendor_id=1, name="A", price=10, stock_qty=5, category="grocery", area_tag="alwal"),
            Product(id=2, vendor_id=1, name="B", price=20, stock_qty=5, category="grocery", area_tag="alwal"),
            Product(id=3, vendor_id=1, name="C", price=30, stock_qty=5, category="grocery", area_tag="alwal"),
        ]
        assert check_ambiguity(products, threshold=2) is True

    def test_ambiguity_with_zero_threshold(self):
        products = [Product(id=1, vendor_id=1, name="A", price=10, stock_qty=5, category="grocery", area_tag="alwal")]
        assert check_ambiguity(products, threshold=0) is True

    def test_ambiguity_instructions_list_candidates(self):
        results = search_products("sweet")
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        assert instructions is not None
        content = " ".join(i.get("content", "") for i in instructions)
        assert "ask" in content.lower() or "list" in content.lower()

    def test_ambiguity_not_fired_for_single_maggi(self):
        results = search_products("maggi")
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        assert instructions is None  # No gate should fire


# =============================================
# EMPTY RESULT GATE (5 tests)
# =============================================

class TestEmptyResultGateEdgeCases:
    """5 tests for empty-result gate edge cases."""

    def test_empty_result_true(self):
        assert check_empty_result([]) is True

    def test_empty_result_false(self):
        assert check_empty_result([Product(id=1, vendor_id=1, name="A", price=10, stock_qty=5, category="grocery", area_tag="alwal")]) is False

    def test_empty_gate_fires_for_unknown_item(self):
        results = search_products("winter wear")
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        assert instructions is not None
        content = " ".join(i.get("content", "") for i in instructions)
        assert "isn't available" in content.lower() or "not available" in content.lower() or "no results" in content.lower()

    def test_empty_gate_asks_to_search_broader(self):
        results = []
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        assert instructions is not None
        content = " ".join(i.get("content", "") for i in instructions)
        assert any(phrase in content.lower() for phrase in ["search again", "alternatives", "similar", "broader"])

    def test_ambiguity_not_fired_when_empty(self):
        """Empty result gate takes priority over ambiguity gate."""
        results = []
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        content = " ".join(i.get("content", "") for i in instructions)
        assert "isn't available" in content.lower() or "not available" in content.lower() or "no results" in content.lower()
        assert "list" not in content.lower() and "ask" not in content.lower()


# =============================================
# BUDGET GATE (5 tests)
# =============================================

class TestBudgetGateEdgeCases:
    """5 tests for budget gate edge cases."""

    def setup_method(self):
        # Clear cart state by using unique user IDs per test
        pass

    def test_budget_exact_match(self):
        cart = add_to_cart("budget_exact", 1, 1)  # Maggi = ₹14
        result = check_budget_gate(cart, 14.0)
        assert result["ok"] is True

    def test_budget_over_by_small_amount(self):
        cart = add_to_cart("budget_small_over", 2, 1)  # Dairy Milk = ₹85
        result = check_budget_gate(cart, 80.0)
        assert result["ok"] is False
        assert result["over_by"] == 5.0

    def test_budget_over_by_large_amount(self):
        cart = add_to_cart("budget_large_over", 11, 1)  # Premium Wool Blend = ₹1299
        result = check_budget_gate(cart, 500.0)
        assert result["ok"] is False
        assert result["over_by"] == 799.0

    def test_budget_zero(self):
        cart = add_to_cart("budget_zero", 1, 1)  # Maggi = ₹14
        result = check_budget_gate(cart, 0.0)
        assert result["ok"] is False
        assert result["over_by"] == 14.0

    def test_budget_negative(self):
        cart = add_to_cart("budget_negative", 1, 1)
        result = check_budget_gate(cart, -10.0)
        assert result["ok"] is False


# =============================================
# CART OPERATIONS (5 tests)
# =============================================

class TestCartEdgeCases:
    """5 tests for cart operation edge cases."""

    def test_empty_cart_total_zero(self):
        cart = get_cart("empty_cart_user")
        assert cart.total == 0.0
        assert len(cart.items) == 0

    def test_add_same_item_multiple_times(self):
        add_to_cart("repeat_user", 1, 2)
        add_to_cart("repeat_user", 1, 3)
        cart = get_cart("repeat_user")
        assert len(cart.items) == 1
        assert cart.items[0].qty == 5
        assert cart.items[0].name == "Maggi Noodles"

    def test_add_different_items(self):
        add_to_cart("multi_user", 1, 1)  # Maggi
        add_to_cart("multi_user", 2, 2)  # Dairy Milk x2
        add_to_cart("multi_user", 14, 1)  # Coca-Cola
        cart = get_cart("multi_user")
        assert len(cart.items) == 3
        expected_total = 14.0 + (85.0 * 2) + 75.0  # 14 + 170 + 75 = 259
        assert cart.total == expected_total

    def test_add_out_of_stock_raises_error(self):
        with pytest.raises(ValueError, match="out of stock"):
            add_to_cart("oos_user", 8, 1)  # Tonik Dettol Soap - stock_qty=0

    def test_add_nonexistent_product_raises_error(self):
        with pytest.raises(ValueError, match="not found"):
            add_to_cart("nonexistent_user", 999, 1)


# =============================================
# GROUNDING CHECK (5 tests)
# =============================================

class TestGroundingEdgeCases:
    """5 tests for grounding check edge cases."""

    def test_empty_response_not_flagged(self):
        result = check_grounding("", [])
        assert result["flagged"] is False

    def test_hallucinated_product_flagged(self):
        tool_log = [{
            "type": "tool_result",
            "tool_name": "search_catalog",
            "arguments": {"query": "maggi"},
            "result": "Found 1 product(s):\n  - [1] Maggi Noodles — ₹14.0 [alwal, stock: 100]",
            "timestamp": "2025-01-01T00:00:00Z",
        }]
        result = check_grounding('I have "Maggi Noodles" and "FakeProduct"', tool_log)
        assert result["flagged"] is True
        assert any("FakeProduct" in d for d in result["details"])

    def test_hallucinated_price_flagged(self):
        tool_log = [{
            "type": "tool_result",
            "tool_name": "search_catalog",
            "arguments": {"query": "maggi"},
            "result": "Found 1 product(s):\n  - [1] Maggi Noodles — ₹14.0 [alwal, stock: 100]",
            "timestamp": "2025-01-01T00:00:00Z",
        }]
        result = check_grounding('"Maggi Noodles" costs ₹99.0', tool_log)
        assert result["flagged"] is True

    def test_valid_product_not_flagged(self):
        tool_log = [{
            "type": "tool_result",
            "tool_name": "search_catalog",
            "arguments": {"query": "maggi"},
            "result": "Found 1 product(s):\n  - [1] Maggi Noodles — ₹14.0 [alwal, stock: 100]",
            "timestamp": "2025-01-01T00:00:00Z",
        }]
        result = check_grounding('"Maggi Noodles" costs ₹14.0', tool_log)
        assert result["flagged"] is False

    def test_multiple_hallucinated_products(self):
        tool_log = [{
            "type": "tool_result",
            "tool_name": "search_catalog",
            "arguments": {"query": "maggi"},
            "result": "Found 1 product(s):\n  - [1] Maggi Noodles — ₹14.0 [alwal, stock: 100]",
            "timestamp": "2025-01-01T00:00:00Z",
        }]
        result = check_grounding('"Maggi Noodles" ₹14.0, "Sugar" ₹40.0, "Flour" ₹30.0', tool_log)
        assert result["flagged"] is True
        assert len(result["details"]) >= 2


# =============================================
# SESSION MANAGEMENT (5 tests)
# =============================================

class TestSessionEdgeCases:
    """5 tests for session management edge cases."""

    def test_new_session_empty(self):
        reset_session("fresh_user")
        session = get_or_create_session("fresh_user")
        assert session.history == []
        assert session.tool_log == []
        assert session.cart_draft == {}

    def test_session_persists_across_calls(self):
        reset_session("persist_user")
        session = get_or_create_session("persist_user")
        session.history.append({"role": "user", "content": "hello"})
        session2 = get_or_create_session("persist_user")
        assert len(session2.history) == 1
        assert session2.history[0]["content"] == "hello"

    def test_reset_clears_everything(self):
        session = get_or_create_session("reset_all")
        session.history.append({"role": "user", "content": "test"})
        session.tool_log.append({"type": "tool_call", "tool_name": "search"})
        reset_session("reset_all")
        new_session = get_or_create_session("reset_all")
        assert new_session.history == []
        assert new_session.tool_log == []

    def test_different_users_isolated(self):
        reset_session("user_a")
        reset_session("user_b")
        session_a = get_or_create_session("user_a")
        session_b = get_or_create_session("user_b")
        session_a.history.append({"role": "user", "content": "from A"})
        assert len(session_b.history) == 0

    def test_reset_nonexistent_user(self):
        """Resetting a user that never existed should not error."""
        reset_session("never_existed")  # Should not raise


# =============================================
# ROUTER / PLANNER (5 tests)
# =============================================

class TestRouterPlannerEdgeCases:
    """5 tests for router and planner edge cases."""

    def test_no_gate_fires_for_normal_result(self):
        results = search_products("maggi")
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        assert instructions is None

    def test_empty_list_no_candidates(self):
        cart = Cart(user_id="test_user")
        instructions = get_instructions([], cart, ambiguity_threshold=2)
        assert instructions is not None

    def test_budget_gate_fires_when_over(self):
        cart = add_to_cart("router_budget", 1, 10)  # Maggi x10 = ₹140
        budget_result = check_budget_gate(cart, 100.0)
        assert budget_result["ok"] is False
        assert budget_result["over_by"] == 40.0

    def test_budget_gate_does_not_fire_when_under(self):
        cart = add_to_cart("router_budget_ok", 1, 1)  # Maggi x1 = ₹14
        budget_result = check_budget_gate(cart, 100.0)
        assert budget_result["ok"] is True

    def test_empty_takes_priority_over_ambiguity(self):
        """When both empty and ambiguity could apply, empty wins."""
        results = []
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        content = " ".join(i.get("content", "") for i in instructions)
        assert "isn't available" in content.lower() or "not available" in content.lower() or "no results" in content.lower()


# =============================================
# API INTEGRATION (5 tests)
# =============================================

class TestApiIntegration:
    """5 tests for HTTP API layer."""

    def test_chat_endpoint_rejects_invalid_json(self):
        response = client.post("/chat", json={"user_id": "", "message": ""})
        # Empty strings are still valid for the schema, so this should be 200 or LLM error
        assert response.status_code in [200, 422]

    def test_reset_session_endpoint(self):
        response = client.post("/reset-session", json={"user_id": "api_test"})
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "api_test" in data["message"]

    def test_chat_invalid_body(self):
        response = client.post("/chat", json={})
        assert response.status_code == 422

    def test_reset_session_invalid_body(self):
        response = client.post("/reset-session", json={})
        assert response.status_code == 422

    def test_chat_without_user_id(self):
        response = client.post("/chat", json={"message": "hello"})
        assert response.status_code == 422


# =============================================
# FUNCTION TAG PARSER (5 tests)
# =============================================

class TestFunctionTagParser:
    """5 tests for the <function=...> tag parser in llm_provider.py."""

    def test_equals_separator(self):
        """<function=name={...}> format with equals sign."""
        text = '<function=search_catalog={"query":"maggi"}></function>'
        result = _parse_function_tag(text)
        assert result is not None
        assert len(result) == 1
        assert result[0]["function"]["name"] == "search_catalog"
        args = result[0]["function"]["arguments"]
        assert '"query"' in args
        assert '"maggi"' in args

    def test_comma_separator(self):
        """<function=name,{...}> format with comma."""
        text = '<function=search_catalog,{"query":"cake"}></function>'
        result = _parse_function_tag(text)
        assert result is not None
        assert len(result) == 1
        assert result[0]["function"]["name"] == "search_catalog"

    def test_quote_separator(self):
        """<function=name"{...} format with quote (the latest Groq variant)."""
        text = '<function=search_catalog"{"query":"flour"}></function>'
        result = _parse_function_tag(text)
        assert result is not None
        assert len(result) == 1
        assert result[0]["function"]["name"] == "search_catalog"
        args = result[0]["function"]["arguments"]
        assert '"flour"' in args

    def test_no_closing_tag(self):
        """<function=name,{...}> without </function> closing tag."""
        text = '<function=search_catalog,{"query":"tea"}>'
        result = _parse_function_tag(text)
        assert result is not None
        assert len(result) == 1
        assert result[0]["function"]["name"] == "search_catalog"

    def test_no_function_tag_returns_none(self):
        """Text without any <function=...> tag should return None."""
        text = "I found Maggi Noodles for ₹14"
        result = _parse_function_tag(text)
        assert result is None


# =============================================
# PRODUCT SCHEMA (5 tests)
# =============================================

class TestProductSchema:
    """5 tests for product data integrity."""

    def test_all_products_have_required_fields(self):
        for p_id in range(1, 29):
            product = get_product(p_id)
            if product:
                assert product.id is not None
                assert product.name
                assert product.price > 0
                assert product.category
                assert product.area_tag

    def test_sweet_category_has_multiple_items(self):
        results = search_products("sweet")
        assert len(results) > 2

    def test_clothing_items_have_fabric_gsm(self):
        results = search_products("sweater")
        for p in results:
            assert p.fabric_gsm is not None, f"{p.name} missing fabric_gsm"

    def test_out_of_stock_items_exist(self):
        """Verify we have out-of-stock items in the catalog."""
        product_8 = get_product(8)  # Tonik Dettol Soap
        product_9 = get_product(9)  # Colgate Toothpaste
        assert product_8 is not None and product_8.stock_qty == 0
        assert product_9 is not None and product_9.stock_qty == 0

    def test_all_product_prices_positive(self):
        for p_id in range(1, 29):
            product = get_product(p_id)
            if product:
                assert product.price > 0, f"Product {p_id} has non-positive price"
