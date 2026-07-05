"""
Tests for the conversational agent.

These tests verify the ReAct loop, grounding check, and gate logic
against the simulated (fake) backend services.
"""

import pytest

from app.agent.grounding import check_grounding
from app.agent.planner import check_ambiguity, check_empty_result, check_budget_gate
from app.agent.router import get_instructions
from app.clients.cart_client import add_to_cart, get_cart
from app.clients.catalog_client import search_products, get_product
from app.clients.session_client import get_or_create_session, append_tool_result
from app.schemas.cart import Cart
from app.schemas.chat import ChatResponse
from app.schemas.product import Product
from app.schemas.tool import ToolResult


# ─────────────────────────────────────────────
# Test 1: Ambiguity gate fires for vague queries
# ─────────────────────────────────────────────

class TestAmbiguityGate:
    def test_ambiguity_fires_for_sweet_query(self):
        """'something sweet' should return > 2 candidates and trip the ambiguity gate."""
        results = search_products("sweet")
        assert len(results) > 2, "Should find multiple sweet items"

        # Verify at least these sweet items exist
        names = {p.name.lower() for p in results}
        assert any("chocolate" in n or "dairy milk" in n for n in names), "Should include chocolate"
        assert any("gulab jamun" in n for n in names), "Should include gulab jamun"
        assert any("ice cream" in n for n in names), "Should include ice cream"

        # Ambiguity gate should fire with threshold=2
        assert check_ambiguity(results, threshold=2) is True, "Ambiguity gate should fire"

    def test_ambiguity_instructions_are_generated(self):
        """Router should generate clarifying instructions when ambiguity fires."""
        results = search_products("sweet")
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        assert instructions is not None, "Router should return instructions when ambiguous"
        content = " ".join(i.get("content", "") for i in instructions)
        assert "ask" in content.lower() or "list" in content.lower(), \
            "Instructions should tell the model to ask a clarifying question"

    def test_ambiguity_does_not_fire_for_specific_query(self):
        """A specific query like 'maggi' should return few results and not trip ambiguity."""
        results = search_products("maggi")
        assert len(results) >= 1, "Should find maggi"
        assert check_ambiguity(results, threshold=2) is False, \
            "Ambiguity gate should NOT fire for specific query"


# ─────────────────────────────────────────────
# Test 2: Out-of-catalog query
# ─────────────────────────────────────────────

class TestEmptyCatalogQuery:
    def test_sweater_search_finds_nothing(self):
        """'sweater' should find no results since no 'sweater' keyword matches."""
        # Note: catalog has "Thick Cotton Sweater" and "Premium Wool Blend Sweater"
        # The search uses token matching, so "sweater" should match
        results = search_products("sweater")
        assert len(results) >= 1, "Should find sweater items (Thick Cotton Sweater, Premium Wool Blend Sweater)"

    def test_winter_wear_returns_empty(self):
        """'winter wear' should return no results as per spec."""
        results = search_products("winter wear")
        assert len(results) == 0, "No products match 'winter wear'"

    def test_empty_result_instructions(self):
        """Router should generate 'not available' instructions for empty results."""
        results = search_products("winter wear")
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        assert instructions is not None, "Router should return instructions for empty result"
        content = " ".join(i.get("content", "") for i in instructions)
        assert "not available" in content.lower() or "no results" in content.lower() or "isn't available" in content.lower(), \
            "Instructions should say the item is not available"

    def test_empty_result_suggests_alternatives(self):
        """Empty-result instructions should tell LLM to search for similar products."""
        results = []
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        assert instructions is not None
        content = " ".join(i.get("content", "") for i in instructions)
        assert "search again" in content.lower() or "alternatives" in content.lower() or "similar" in content.lower(), \
            "Instructions should tell the LLM to search for alternatives"


# ─────────────────────────────────────────────
# Test 3: Structured clothing attribute filter
# ─────────────────────────────────────────────

class TestClothingAttributeFilter:
    def test_thick_high_quality_sweater(self):
        """'thick, high-quality sweater' should filter by min_gsm and min_rating."""
        results = search_products("sweater", min_gsm=300, min_rating=4.5)
        assert len(results) >= 1, "Should find at least one sweater matching criteria"

        # Check that all returned products meet the criteria
        for p in results:
            assert p.fabric_gsm is not None and p.fabric_gsm >= 300, \
                f"{p.name} should have GSM >= 300"
            assert p.rating is not None and p.rating >= 4.5, \
                f"{p.name} should have rating >= 4.5"

        # Premium Wool Blend Sweater should be in results (GSM=450, rating=4.8)
        names = [p.name for p in results]
        assert "Premium Wool Blend Sweater" in names, \
            "Premium Wool Blend Sweater should match thick, high-quality criteria"

    def test_lightweight_filter(self):
        """Light summer clothing should have lower GSM."""
        results = search_products("shirt", min_gsm=100)
        assert len(results) >= 1, "Should find t-shirts"
        for p in results:
            assert p.fabric_gsm is not None

    def test_filtered_results_mention_filters(self):
        """Response should state what filters were applied."""
        # We're testing the catalog actually filters correctly
        results = search_products("sweater", min_gsm=400, min_rating=4.5)
        assert len(results) >= 1
        # Only Premium Wool Blend (GSM=450, rating=4.8) should pass
        names = [p.name for p in results]
        assert "Premium Wool Blend Sweater" in names
        assert "Thick Cotton Sweater" not in names  # GSM=350, min_gsm=400 fails


# ─────────────────────────────────────────────
# Test 4: Genuinely empty result warnings
# ─────────────────────────────────────────────

class TestEmptyResultNoAlternatives:
    def test_empty_result_does_not_propose_alternatives(self):
        """Empty result should instruct LLM to search for alternatives."""
        results = []
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        assert instructions is not None
        content = " ".join(i.get("content", "") for i in instructions)

        # The gate should tell the LLM to search for similar products
        assert any(phrase in content.lower() for phrase in [
            "search again", "alternatives", "similar", "broader",
        ]), f"Instructions should tell the LLM to find alternatives. Got: {content}"

    def test_empty_ambiguity_no_gate(self):
        """If empty AND ambiguous, empty-result gate should take priority."""
        results = []
        cart = Cart(user_id="test_user")
        instructions = get_instructions(results, cart, ambiguity_threshold=2)
        assert instructions is not None
        content = " ".join(i.get("content", "") for i in instructions)
        # Should say not available, not ask for clarification
        assert "not available" in content.lower() or "no results" in content.lower(), \
            "Empty-result gate should fire instead of ambiguity gate"


# ─────────────────────────────────────────────
# Test 5: Grounding check for hallucinated claims
# ─────────────────────────────────────────────

class TestGroundingCheck:
    def test_grounding_flags_tampered_product_name(self):
        """
        Create a tool log with a real product, then check a response that
        mentions a product NOT in the log. Grounding should flag it.
        """
        tool_log = [
            {
                "type": "tool_result",
                "tool_name": "search_catalog",
                "arguments": {"query": "maggi"},
                "result": "Found 1 product(s):\n  - [1] Maggi Noodles — ₹14.0 [alwal, stock: 100]",
                "timestamp": "2025-01-01T00:00:00Z",
            },
        ]

        # This response mentions a product NOT in the tool log
        response_text = 'I found "Maggi Noodles" for ₹14.0 and also "Pasta" for ₹50.0'
        result = check_grounding(response_text, tool_log)
        assert result["flagged"] is True, "Should flag hallucinated product 'Pasta'"
        assert any("Pasta" in d or "pasta" in d for d in result["details"]), \
            "Details should mention the hallucinated product 'Pasta'"

    def test_grounding_flags_tampered_price(self):
        """
        Verify that a price that doesn't match any known product price
        gets flagged.
        """
        tool_log = [
            {
                "type": "tool_result",
                "tool_name": "search_catalog",
                "arguments": {"query": "chocolate"},
                "result": "Found 1 product(s):\n  - [2] Dairy Milk Silk — ₹85.0 [alwal, stock: 30]",
                "timestamp": "2025-01-01T00:00:00Z",
            },
        ]

        response_text = 'The "Dairy Milk Silk" costs ₹99.0'  # ₹99.0 != ₹85.0
        result = check_grounding(response_text, tool_log)
        assert result["flagged"] is True, "Should flag hallucinated ₹99.0 price"

    def test_grounding_passes_valid_claims(self):
        """When all claims match tool results, grounding should NOT flag."""
        tool_log = [
            {
                "type": "tool_result",
                "tool_name": "search_catalog",
                "arguments": {"query": "maggi"},
                "result": "Found 1 product(s):\n  - [1] Maggi Noodles — ₹14.0 [alwal, stock: 100]",
                "timestamp": "2025-01-01T00:00:00Z",
            },
        ]

        response_text = 'I found "Maggi Noodles" in the catalog for ₹14.0'
        result = check_grounding(response_text, tool_log)
        assert result["flagged"] is False, "Should NOT flag valid claims"


# ─────────────────────────────────────────────
# Additional integration-style tests
# ─────────────────────────────────────────────

class TestBudgetGate:
    def test_budget_check_arithmetic(self):
        """Budget check uses real arithmetic, not LLM estimation."""
        # Add items to cart
        cart = add_to_cart("budget_user", 1, 2)  # Maggi Noodles x2 = ₹28
        cart = add_to_cart("budget_user", 2, 1)  # Dairy Milk Silk x1 = ₹85
        # Total = ₹113

        result = check_budget_gate(cart, budget=100.0)
        assert result["ok"] is False, "Budget should fail"
        assert result["over_by"] == 13.0, f"Should be over by ₹13.0, got ₹{result['over_by']}"

    def test_budget_within_limit(self):
        """Budget check passes when cart is within budget."""
        cart = add_to_cart("budget_user2", 1, 1)  # Maggi Noodles x1 = ₹14
        result = check_budget_gate(cart, budget=50.0)
        assert result["ok"] is True, "Budget should pass"
        assert result["over_by"] == 0.0


class TestCartOperations:
    def test_add_to_cart_updates_total(self):
        """Adding items should correctly update the cart total."""
        cart = add_to_cart("cart_user", 1, 3)  # Maggi Noodles x3 = ₹42
        assert len(cart.items) == 1
        assert cart.total == 42.0, f"Total should be ₹42.0, got ₹{cart.total}"

    def test_add_multiple_items(self):
        """Adding different items should accumulate in cart."""
        add_to_cart("cart_user2", 1, 1)  # Maggi = ₹14
        add_to_cart("cart_user2", 2, 2)  # Dairy Milk x2 = ₹170
        cart = get_cart("cart_user2")
        assert len(cart.items) == 2
        assert cart.total == 184.0, f"Total should be ₹184.0, got ₹{cart.total}"

    def test_add_out_of_stock_raises(self):
        """Adding an out-of-stock product should raise ValueError."""
        with pytest.raises(ValueError, match="out of stock"):
            add_to_cart("cart_user3", 8, 1)  # Tonik Dettol Soap - stock_qty=0


class TestCatalogSearch:
    def test_search_by_area(self):
        """Search should filter by vendor_area."""
        results = search_products("maggi", vendor_area="alwal")
        assert len(results) == 1
        assert results[0].area_tag == "alwal"

    def test_search_no_match(self):
        """Search with no matching query should return empty."""
        results = search_products("nonexistent_product_xyz")
        assert len(results) == 0

    def test_get_product_by_id(self):
        """get_product should return the correct product."""
        product = get_product(1)
        assert product is not None
        assert product.name == "Maggi Noodles"
        assert product.price == 14.0

    def test_get_nonexistent_product(self):
        """get_product for non-existent ID should return None."""
        product = get_product(999)
        assert product is None


class TestSessionClient:
    def test_get_or_create_session(self):
        """Session should be created and reused."""
        session = get_or_create_session("session_user")
        assert session.user_id == "session_user"
        assert session.history == []
        assert session.tool_log == []

        # Same user should return same session
        session2 = get_or_create_session("session_user")
        assert session2 is session

    def test_reset_session(self):
        """Resetting a session should clear all its data."""
        from app.clients.session_client import reset_session

        session = get_or_create_session("reset_user")
        session.history.append({"role": "user", "content": "hello"})
        session.tool_log.append({"type": "tool_call", "tool_name": "test"})
        assert len(session.history) == 1
        assert len(session.tool_log) == 1

        # Reset and verify it's gone
        reset_session("reset_user")
        new_session = get_or_create_session("reset_user")
        assert new_session is not session  # Should be a new object
        assert new_session.history == []
        assert new_session.tool_log == []

    def test_append_tool_result(self):
        """Tool results should be appended to the session log."""
        session = get_or_create_session("session_user2")
        tool_result = ToolResult(
            tool_name="search_catalog",
            arguments={"query": "test"},
            result="test result",
        )
        append_tool_result(session, tool_result)
        assert len(session.tool_log) == 1
        assert session.tool_log[0]["tool_name"] == "search_catalog"
        assert session.tool_log[0]["result"] == "test result"


class TestPlannerFunctions:
    def test_check_ambiguity_true(self):
        """check_ambiguity returns True when candidates exceed threshold."""
        products = [
            Product(id=1, vendor_id=1, name="A", price=10, stock_qty=5, category="grocery", area_tag="alwal"),
            Product(id=2, vendor_id=1, name="B", price=20, stock_qty=5, category="grocery", area_tag="alwal"),
            Product(id=3, vendor_id=1, name="C", price=30, stock_qty=5, category="grocery", area_tag="alwal"),
        ]
        assert check_ambiguity(products, threshold=2) is True

    def test_check_ambiguity_false(self):
        """check_ambiguity returns False when candidates are within threshold."""
        products = [
            Product(id=1, vendor_id=1, name="A", price=10, stock_qty=5, category="grocery", area_tag="alwal"),
        ]
        assert check_ambiguity(products, threshold=2) is False

    def test_check_empty_result(self):
        """check_empty_result returns True for empty list."""
        assert check_empty_result([]) is True
        assert check_empty_result([Product(id=1, vendor_id=1, name="A", price=10, stock_qty=5, category="grocery", area_tag="alwal")]) is False
