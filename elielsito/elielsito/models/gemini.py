"""Adaptador para Google Gemini (generateContent).

Nota de honestidad: implementado según la API pública, **no probado contra el
servicio real** por falta de clave en este entorno.
"""

from __future__ import annotations

from typing import Any

from ..http import HttpError, post_json
from .base import Message, ModelAdapter, ModelError, ModelResponse, ToolCall

BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiAdapter(ModelAdapter):
    name = "gemini"

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        *,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: int = 60,
    ):
        if not api_key:
            raise ModelError("Falta GEMINI_API_KEY.")
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
        contents: list[dict[str, Any]] = []
        for message in messages:
            if message.role == "system":
                continue
            role = "model" if message.role == "assistant" else "user"
            parts: list[dict[str, Any]] = []
            if message.content:
                parts.append({"text": message.content})
            for call in message.tool_calls or []:
                parts.append({"functionCall": {"name": call.name, "args": call.arguments}})
            if message.role == "tool":
                parts = [
                    {
                        "functionResponse": {
                            "name": message.name or "tool",
                            "response": {"result": message.content or ""},
                        }
                    }
                ]
            if parts:
                contents.append({"role": role, "parts": parts})

        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": kwargs.get("temperature", self.temperature),
                "maxOutputTokens": kwargs.get("max_tokens", self.max_tokens),
            },
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}
        if tools:
            payload["tools"] = [
                {
                    "functionDeclarations": [
                        {
                            "name": tool["name"],
                            "description": tool.get("description", ""),
                            "parameters": tool.get("parameters", {"type": "object", "properties": {}}),
                        }
                        for tool in tools
                    ]
                }
            ]

        url = f"{BASE_URL}/{self.model}:generateContent?key={self.api_key}"
        try:
            data = post_json(url, payload, timeout=self.timeout)
        except HttpError as exc:
            raise ModelError(f"Gemini falló: {exc}") from exc

        return self._parse(data)

    def _parse(self, data: dict[str, Any]) -> ModelResponse:
        candidates = data.get("candidates") or []
        if not candidates:
            raise ModelError(f"Gemini no devolvió candidatos: {data}")
        parts = (candidates[0].get("content") or {}).get("parts") or []
        texts: list[str] = []
        tool_calls: list[ToolCall] = []
        for index, part in enumerate(parts):
            if "text" in part:
                texts.append(part["text"])
            elif "functionCall" in part:
                call = part["functionCall"]
                tool_calls.append(
                    ToolCall(id=f"gemini_{index}", name=call.get("name", ""), arguments=call.get("args") or {})
                )
        return ModelResponse(
            content="\n".join(filter(None, texts)),
            tool_calls=tool_calls,
            model=self.model,
            finish_reason=candidates[0].get("finishReason"),
            usage=data.get("usageMetadata"),
        )
