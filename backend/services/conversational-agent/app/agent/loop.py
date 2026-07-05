import json
import re
import traceback
from datetime import datetime, timezone

from loguru import logger

from app.agent.grounding import check_grounding
from app.agent.llm_provider import get_provider
from app.agent.router import get_instructions
from app.agent.state import AgentState
from app.agent.tool_registry import get_all_schemas, get_dispatch_map
from app.clients.cart_client import add_to_cart as _add_to_cart, get_cart
from app.clients.session_client import append_tool_call, append_tool_result
from app.schemas.cart import Cart
from app.schemas.chat import ChatResponse
from app.schemas.tool import ToolCall, ToolResult
from app.core.config import settings
from app.core.prompts import SYSTEM_PROMPT


def _parse_tool_arguments(arguments: str | dict) -> dict:
    if isinstance(arguments, dict):
        return arguments
    try:
        return json.loads(arguments)
    except (json.JSONDecodeError, TypeError):
        logger.warning(f"Failed to parse tool arguments: {arguments}")
        return {}


def run_agent(state: AgentState, user_message: str) -> ChatResponse:
    """
    The ReAct loop:

    1. Send state.history + tool schemas to the LLM provider
    2. If response is tool call → execute it, log to tool_log, run planner/ router, loop
    3. If response is final text → run grounding check, return ChatResponse
    """
    provider = get_provider()
    dispatch = get_dispatch_map()
    tool_schemas = get_all_schemas()
    cart = get_cart(state.user_id)

    # Track budget if mentioned in user message
    budget: float | None = None
    # Simple heuristic: extract budget amount if user mentions "budget" followed by a number
    budget_match = re.search(r"budget\s*[₹]?\s*(\d+(?:\.\d+)?)", user_message, re.IGNORECASE)
    if budget_match:
        budget = float(budget_match.group(1))

    # Inject system prompt to guide LLM behavior (only once per session)
    if not any(msg.get("role") == "system" for msg in state.history):
        state.append_to_history({
            "role": "system",
            "content": SYSTEM_PROMPT,
        })

    # Append user message to history
    state.append_to_history({"role": "user", "content": user_message})

    # Max turns to prevent infinite loops — keeps latency manageable
    max_turns = 5
    turn = 0

    while turn < max_turns:
        turn += 1
        logger.debug(f"Agent loop turn {turn} for user {state.user_id}")

        # Call LLM
        try:
            response = provider.chat_completion(
                messages=state.history,
                tools=tool_schemas,
            )
        except Exception as e:
            logger.error(f"LLM provider error: {e}\n{traceback.format_exc()}")
            return ChatResponse(
                response="I'm sorry, I encountered an error processing your request. Please try again.",
                cart=cart,
                flagged_hallucination=False,
            )

        assistant_content = response.get("content") or ""
        tool_calls = response.get("tool_calls")

        # If no tool calls → LLM wants to respond with final text
        if not tool_calls:
            # Detect when the LLM talks about adding to cart without actually calling the function
            # This happens when the text fallback model outputs natural language instead of <function=...> tags
            # Supports English, Hindi, Hinglish, and Telugu variants
            mentions_cart_actions = any(
                phrase in assistant_content.lower()
                for phrase in [
                    # English
                    "added to cart", "added to your cart", "was added", "were added", "has been added",
                    # Hindi / Hinglish
                    "add kar diya", "add kar diye", "add kiya", "add kiye",
                    "cart mein add", "cart mei add",
                    "add ho gaya", "add ho gaye",
                    "cart mein daal", "cart mei daal",
                    "dal diya", "dal diye", "daal diya",
                    "kharid liya", "kharid liye",
                    "le liya", "le liye",
                    # Telugu
                    "kalinchindi", "kalinchamu",  # added
                    "konnaru", "tisukunnaru",  # purchased/took
                ]
            )
            # Scan backward through history to find the last REAL user message (not system/gate injections)
            last_real_user = ""
            for msg in reversed(state.history):
                if msg.get("role") == "user" and not msg.get("content", "").startswith("[SYSTEM:"):
                    last_real_user = msg.get("content", "")
                    break
            user_requested_cart = any(
                phrase in last_real_user.lower()
                for phrase in [
                    # English
                    "add", "cart", "purchase", "buy", "order",
                    # Hindi / Hinglish
                    "daal do", "dal do", "daal de", "dal de",
                    "kharido", "kharid lo", "kharid",
                    "mangao", "manga do",
                    "le lo", "le aao", "lao",
                    # Telugu
                    "konali", "konu",  # need to buy
                    "koni ra", "koni randi",  # bring/buy
                    "kalinchu",  # add
                ]
            ) if last_real_user else False

            if mentions_cart_actions and user_requested_cart:
                logger.warning(f"LLM claimed cart action without calling function on turn {turn}, auto-adding items from search results")
                # Instead of relying on the LLM (which keeps failing), parse the search results
                # from the conversation history and auto-execute add_to_cart.
                # Only add products whose IDs appear in the assistant's response text ([id] pattern).
                # This prevents adding ALL search results — only what the model actually mentioned.
                # First, find all product IDs and names from search results in history
                catalog_products: dict[int, str] = {}  # product_id -> name
                for msg in state.history:
                    if msg.get("role") == "tool" and msg.get("name") == "search_catalog":
                        content = msg.get("content", "")
                        for match in re.finditer(r"\[(\d+)\]\s*(.+?)\s*[—–-]\s*[₹Rs.]*[\d.]+", content):
                            pid = int(match.group(1))
                            name = match.group(2).strip()
                            catalog_products[pid] = name

                # Then check which of those IDs appear in the assistant's response
                already_in_cart = {item.product_id for item in cart.items}
                added_items = []
                for pid, pname in catalog_products.items():
                    # Only add if product is mentioned by ID in the response and not already in cart
                    if f"[{pid}]" in assistant_content and pid not in already_in_cart:
                        try:
                            updated_cart = _add_to_cart(state.user_id, pid, 1)
                            added_items.append(pname)
                            cart = updated_cart
                            already_in_cart.add(pid)  # prevent re-adding in this batch
                            logger.info(f"Auto-added '{pname}' (ID {pid}) to cart for user {state.user_id}")
                        except ValueError as e:
                            logger.warning(f"Failed to auto-add product {pid} ({pname}): {e}")

                if added_items:
                    items_str = ", ".join(added_items)
                    state.append_to_history({
                        "role": "user",
                        "content": f"[SYSTEM: The following items were automatically added to cart: {items_str}. Current cart total: ₹{cart.total}. Tell the user these were added successfully.]",
                    })
                    continue

                # If we're on the last turn and couldn't auto-add, warn the user
                if turn >= max_turns - 1:
                    logger.warning("Last turn reached with unfulfilled cart action, returning clarifying message")
                    state.append_to_history({
                        "role": "assistant",
                        "content": "I wasn't able to add the items to your cart. Could you please try again or use the 'Add' button next to the product instead?",
                    })
                    return ChatResponse(
                        response="I wasn't able to add the items to your cart. Could you please try again or use the 'Add' button next to the product instead?",
                        cart=cart,
                        flagged_hallucination=False,
                    )

                # Fall back to asking the model to retry
                state.append_to_history({
                    "role": "user",
                    "content": "[SYSTEM: You said items were added to cart, but no function was actually called. Please call the add_to_cart function using the format <function=add_to_cart,{\"user_id\": \"...\", \"product_id\": X}> to actually add items.]",
                })
                continue

            # Append assistant message to history
            state.append_to_history({
                "role": "assistant",
                "content": assistant_content,
            })

            # Run grounding check before returning
            grounding_result = check_grounding(assistant_content, state.tool_log)

            if grounding_result["flagged"]:
                logger.warning(
                    f"Hallucination flagged for user {state.user_id}: "
                    f"{grounding_result['details']}"
                )

            return ChatResponse(
                response=assistant_content,
                cart=get_cart(state.user_id),
                flagged_hallucination=grounding_result["flagged"],
            )

        # Log all tool calls and results first
        tool_call_entries = []
        tool_result_entries = []
        # Accumulate ALL search results from this turn for proper gate checks
        turn_search_candidates = {}

        for tc in tool_calls:
            function_info = tc.get("function", {})
            tool_name = function_info.get("name", "")
            raw_arguments = function_info.get("arguments", "{}")
            arguments = _parse_tool_arguments(raw_arguments)

            # Log the tool call
            tool_call_obj = ToolCall(name=tool_name, arguments=arguments)
            append_tool_call(state._session, tool_call_obj)
            tool_call_entries.append(tc)

            # Execute the tool
            handler = dispatch.get(tool_name)
            if handler is None:
                result_str = f"Unknown tool: {tool_name}"
                logger.warning(result_str)
            else:
                try:
                    handler_kwargs = dict(arguments)
                    result_str = handler(**handler_kwargs)
                except Exception as e:
                    result_str = f"Error executing {tool_name}: {e}"
                    logger.error(f"Tool execution error: {e}\n{traceback.format_exc()}")

            # Log the tool result
            tool_result_obj = ToolResult(
                tool_name=tool_name,
                arguments=arguments,
                result=result_str,
                timestamp=datetime.now(tz=timezone.utc).isoformat(),
            )
            append_tool_result(state._session, tool_result_obj)
            tool_result_entries.append({
                "tool_call_id": tc.get("id", ""),
                "name": tool_name,
                "content": result_str,
            })

            # Track search results for gate checks — accumulate ALL searches in this turn
            if tool_name == "search_catalog":
                if "No products found" not in result_str:
                    from app.clients.catalog_client import search_products
                    turn_results = search_products(
                        query=arguments.get("query", ""),
                        vendor_area=arguments.get("vendor_area"),
                        min_gsm=arguments.get("min_gsm"),
                        min_rating=arguments.get("min_rating"),
                        max_price=arguments.get("max_price"),
                    )
                    for p in turn_results:
                        turn_search_candidates[p.id] = p

        # Add single assistant message with all tool calls and any text
        state.append_to_history({
            "role": "assistant",
            "content": assistant_content or None,
            "tool_calls": tool_call_entries,
        })

        # Add tool result messages
        for entry in tool_result_entries:
            state.append_to_history({
                "role": "tool",
                "tool_call_id": entry["tool_call_id"],
                "name": entry["name"],
                "content": entry["content"],
            })

        # After all tool calls in this turn, check gates against accumulated search results
        cart = get_cart(state.user_id)
        gate_instructions = get_instructions(
            search_candidates=list(turn_search_candidates.values()),
            cart=cart,
            ambiguity_threshold=settings.ambiguity_threshold,
            budget=budget,
        )

        if gate_instructions:
            for instruction in gate_instructions:
                state.append_to_history(instruction)
            budget = None  # cleared budget gate after firing

    # If we exceed max turns
    logger.warning(f"Agent loop exceeded max turns ({max_turns}) for user {state.user_id}")
    return ChatResponse(
        response="I've been thinking about this for a while. Could you please clarify or simplify your request?",
        cart=get_cart(state.user_id),
        flagged_hallucination=False,
    )
