"""
Thin interface for LLM providers.

Currently implements Groq (OpenAI-compatible API).
Adding a new provider means adding a class in this file that implements
the same `chat_completion` signature.
"""

import json
import re
from abc import ABC, abstractmethod

from loguru import logger

from app.core.config import settings


def _parse_function_tag(text: str) -> list[dict] | None:
    """
    Parse <function=name...JSON...> tags from model text output.

    Groq's Llama models sometimes output function calls in a custom XML-like format
    instead of the standard OpenAI tool_calls format. This parser handles all
    known variants:
      - <function=name={"key":"val"}>
      - <function=name,{"key":"val"}>
      - <function=name{"key":"val"}>
      - <function=name=JSON</function>
      - <function=name,JSON</function>

    Returns a list of tool_call dicts matching the OpenAI format, or None if
    no function tags were found.
    """
    # Pattern 1: <function=name={"key":"val"}</function> (with or without separators, closed)
    pattern = r"<function=(\w+)[=,:\"]*(\{.*?\})</function>"
    matches = re.findall(pattern, text, re.DOTALL)

    if not matches:
        # Pattern 2: same but without closing tag
        pattern2 = r"<function=(\w+)[=,:\"]*(\{.*?\})"
        matches = re.findall(pattern2, text, re.DOTALL)

    if not matches:
        # Pattern 3: parenthesized JSON — <function=name({"key":"val"})</function>
        pattern3 = r"<function=(\w+)\(\s*(\{.*?\})\s*\)</function>"
        matches = re.findall(pattern3, text, re.DOTALL)

    if not matches:
        # Pattern 4: parenthesized JSON without closing tag
        pattern4 = r"<function=(\w+)\(\s*(\{.*?\})\s*\)"
        matches = re.findall(pattern4, text, re.DOTALL)

    if not matches:
        # Pattern 5: <function=name>{JSON}</function> (uses > instead of =)
        pattern5 = r"<function=(\w+)>\s*(\{.*?\})\s*</function>"
        matches = re.findall(pattern5, text, re.DOTALL)

    if not matches:
        # Pattern 6: <function=name>{JSON} (no closing tag, > separator)
        pattern6 = r"<function=(\w+)>\s*(\{.*?\})"
        matches = re.findall(pattern6, text, re.DOTALL)

    if not matches:
        return None

    tool_calls = []
    for i, (name, args_json) in enumerate(matches):
        try:
            args = json.loads(args_json)
        except json.JSONDecodeError:
            # Try to fix common issues: missing quotes around keys
            try:
                fixed = re.sub(r"(\w+):", r'"\1":', args_json)
                args = json.loads(fixed)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse function arguments: {args_json}")
                continue

        tool_calls.append({
            "id": f"call_fallback_{i}",
            "type": "function",
            "function": {
                "name": name,
                "arguments": json.dumps(args),
            },
        })

    return tool_calls if tool_calls else None


def _build_tool_descriptions(tools: list[dict]) -> str:
    """
    Build a text description of available tools for the system prompt.
    Used as fallback when the tools API parameter doesn't work.
    """
    lines = ["\n\nAVAILABLE TOOLS (respond with <function=TOOL_NAME,JSON> to call a tool):"]
    for tool in tools:
        func = tool.get("function", {})
        name = func.get("name", "")
        desc = func.get("description", "")
        params = func.get("parameters", {}).get("properties", {})
        required = func.get("parameters", {}).get("required", [])

        lines.append(f"\n{name}: {desc}")
        lines.append("  Parameters:")
        for p_name, p_info in params.items():
            p_type = p_info.get("type", "any")
            p_desc = p_info.get("description", "")
            req = " (required)" if p_name in required else ""
            lines.append(f"    - {p_name}: {p_type}{req} — {p_desc}")
        lines.append(f"  Example: <function={name},{'{'}\"{list(params.keys())[0] if params else 'key'}\": \"value\"{'}'}></function>")
    return "\n".join(lines)


class LLMProvider(ABC):
    """Abstract base for an LLM provider."""

    @abstractmethod
    def chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
    ) -> dict:
        """
        Send a chat completion request.

        Returns a dict with keys:
          - "role": "assistant"
          - "content": str | None
          - "tool_calls": list[dict] | None  (each with "id", "type", "function": {"name", "arguments"})
        """
        ...


class GroqProvider(LLMProvider):
    """Groq LLM provider via OpenAI-compatible API."""

    def __init__(self):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Install 'openai' package to use the Groq provider")

        self._client = OpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
        )
        self._model = settings.model_name

    def chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
    ) -> dict:
        # Skip the native tools API — Llama on Groq consistently fails with tool_use_failed.
        # Instead, always use text-based function calling which is faster and more reliable.
        if tools:
            return self._chat_completion_text_fallback(messages, tools)
        # If no tools, use standard chat completion
        return self._chat_completion_with_tools(messages, None, tool_choice)

    def _chat_completion_with_tools(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
    ) -> dict:
        """Standard OpenAI-compatible chat completion with tools parameter."""
        from openai import OpenAI

        kwargs = {
            "model": self._model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice

        response = self._client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message

        result: dict = {
            "role": message.role,
            "content": message.content,
            "tool_calls": None,
        }

        if message.tool_calls:
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]

        return result

    def _chat_completion_text_fallback(
        self,
        messages: list[dict],
        tools: list[dict],
    ) -> dict:
        """
        Fallback: don't use the tools API parameter. Instead, describe tools in
        the system prompt and parse <function=...> tags from the response text.
        """
        # Build tool descriptions
        tool_descriptions = _build_tool_descriptions(tools)

        # Inject tool descriptions into the first system/user message (only once)
        fallback_messages = []
        injected = False
        has_descriptions = any("AVAILABLE TOOLS" in (m.get("content") or "") for m in messages)
        if not has_descriptions:
            for msg in messages:
                m = dict(msg)
                if not injected and m.get("role") in ("system", "user"):
                    m["content"] = (m.get("content") or "") + tool_descriptions
                    injected = True
                fallback_messages.append(m)
            if not injected:
                fallback_messages.insert(0, {
                    "role": "system",
                    "content": tool_descriptions,
                })
        else:
            fallback_messages = [dict(m) for m in messages]

        response = self._client.chat.completions.create(
            model=self._model,
            messages=fallback_messages,
        )

        choice = response.choices[0]
        content = choice.message.content or ""

        result: dict = {
            "role": "assistant",
            "content": content,
            "tool_calls": None,
        }

        # Try to parse <function=...> tags from the text response
        tool_calls = _parse_function_tag(content)
        if tool_calls:
            result["tool_calls"] = tool_calls
            # Strip function tags from displayed content (closed and unclosed variants)
            cleaned = re.sub(r"<function=.*?</function>\s*", "", content, flags=re.DOTALL)
            cleaned = re.sub(r"<function=[^>]*>\s*", "", cleaned, flags=re.DOTALL)
            result["content"] = cleaned.strip()

        return result


class GeminiProvider(LLMProvider):
    """Placeholder for Gemini provider — not yet implemented."""

    def __init__(self):
        raise NotImplementedError("Gemini provider not yet implemented. Set MODEL_PROVIDER=groq to use Groq instead.")

    def chat_completion(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
        tool_choice: str = "auto",
    ) -> dict:
        raise NotImplementedError()


def get_provider() -> LLMProvider:
    """Factory: return the provider based on settings."""
    provider_name = settings.model_provider.lower()

    if provider_name == "groq":
        return GroqProvider()
    elif provider_name == "gemini":
        return GeminiProvider()
    else:
        raise ValueError(f"Unknown model provider: {provider_name}. Supported: groq, gemini")
