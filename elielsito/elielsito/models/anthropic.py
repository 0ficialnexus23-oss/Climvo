"""Adaptador para la API de mensajes de Anthropic (Claude).

Nota de honestidad: implementado según la API pública, **no probado contra el
servicio real** por falta de clave en este entorno.
"""

from __future__ import annotations

from typing import Any

from ..http import HttpError, post_json
from .base import Message, ModelAdapter, ModelError, ModelResponse, ToolCall

API_URL = "https://api.anthropic.com/v1/messages"
API_VERSION = "2023-06-01"


class AnthropicAdapter(ModelAdapter):
    name = "anthropic"

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        *,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: int = 60,
    ):
        if not api_key:
            raise ModelError("Falta ANTHROPIC_API_KEY.")
        self.model = model
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout

    def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        system_parts = [m.content for m in messages if m.role == "system"]
        conversation: list[dict[str, Any]] = []
        for message in messages:
            if message.role == "system":
                continue
            if message.role == "tool":
                conversation.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": message.tool_call_id or "",
                                "content": message.content or "",
                            }
                        ],
                    }
                )
                continue
            if message.role == "assistant" and message.tool_calls:
                blocks: list[dict[str, Any]] = []
                if message.content:
                    blocks.append({"type": "text", "text": message.content})
                for call in message.tool_calls:
                    blocks.append(
                        {"type": "tool_use", "id": call.id, "name": call.name, "input": call.arguments}
                    )
                conversation.append({"role": "assistant", "content": blocks})
                continue
            conversation.append({"role": message.role, "content": message.content or ""})

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "messages": conversation,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        if tools:
            payload["tools"] = [
                {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("parameters", {"type": "object", "properties": {}}),
                }
                for tool in tools
            ]

        try:
            data = post_json(
                API_URL,
                payload,
                headers={"x-api-key": self.api_key, "anthropic-version": API_VERSION},
                timeout=self.timeout,
            )
        except HttpError as exc:
            raise ModelError(f"Anthropic falló: {exc}") from exc

        return self._parse(data)

    def _parse(self, data: dict[str, Any]) -> ModelResponse:
        texts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in data.get("content") or []:
            if block.get("type") == "text":
                texts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    ToolCall(id=block.get("id", ""), name=block.get("name", ""), arguments=block.get("input") or {})
                )
        return ModelResponse(
            content="\n".join(filter(None, texts)),
            tool_calls=tool_calls,
            model=data.get("model") or self.model,
            finish_reason=data.get("stop_reason"),
            usage=data.get("usage"),
        )
