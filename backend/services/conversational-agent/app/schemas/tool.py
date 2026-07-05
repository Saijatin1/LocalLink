from datetime import datetime, timezone

from pydantic import BaseModel


class ToolCall(BaseModel):
    name: str
    arguments: dict


class ToolResult(BaseModel):
    tool_name: str
    arguments: dict
    result: str
    timestamp: str = ""
