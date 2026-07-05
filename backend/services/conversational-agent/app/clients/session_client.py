from datetime import datetime, timezone

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.tool import ToolCall, ToolResult


class SessionData:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.history: list[dict] = []
        self.cart_draft: dict = {}
        self.tool_log: list[dict] = []


_sessions: dict[str, SessionData] = {}


def get_or_create_session(user_id: str) -> SessionData:
    """Get or create a session for the given user. Only file that changes for Redis swap."""
    if user_id not in _sessions:
        _sessions[user_id] = SessionData(user_id)
    return _sessions[user_id]


def append_tool_call(session: SessionData, tool_call: ToolCall) -> None:
    """Append a tool call to the session's tool_log."""
    session.tool_log.append({
        "type": "tool_call",
        "tool_name": tool_call.name,
        "arguments": tool_call.arguments,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    })


def append_tool_result(session: SessionData, tool_result: ToolResult) -> None:
    """Append a tool result to the session's tool_log."""
    session.tool_log.append({
        "type": "tool_result",
        "tool_name": tool_result.tool_name,
        "arguments": tool_result.arguments,
        "result": tool_result.result,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    })


def reset_session(user_id: str) -> None:
    """Delete a session's data. A new empty session will be created on next request."""
    _sessions.pop(user_id, None)
