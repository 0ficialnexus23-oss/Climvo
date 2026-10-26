"""Adaptador para APIs compatibles con OpenAI.

Sirve para OpenAI y también para servidores **locales** que exponen la misma
interfaz (Ollama, LM Studio, llama.cpp, vLLM). Basta con cambiar ``base_url``.
"""

from __future__ import annotations

import json
from typing import Any

from ..http import HttpError, post_json
from .base import Message, ModelAdapter, ModelError, ModelResponse, ToolCall


class OpenAICompatibleAdapter(ModelAdapter):
    name = "openai"

    def __init__(
        self,
        model: str,
        *,
        api_key: str | None = None,
        base_url: str = "https://api.openai.com/v1",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        timeout: int = 60,
        requires_key: bool = True,
        label: str | None = None,
    ):
        if requires_key and not api_key:
            raise ModelError(
                "Falta la clave de API para este proveedor. Configúrala en el "
                "entorno (por ejemplo OPENAI_API_KEY) o usa el proveedor 'ollama'."
            )
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.label = label or self.name

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [m.to_openai() for m in messages],
            "temperature": kwargs.get("temperature", self.temperature),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }
        if tools:
            payload["tools"] = [
                {"type": "function", "function": tool} for tool in tools
            ]
            payload["tool_choice"] = "auto"

        try:
            data = post_json(
                f"{self.base_url}/chat/completions",
                payload,
                headers=self._headers(),
                timeout=self.timeout,
            )
        except HttpError as exc:
            raise ModelError(f"El proveedor '{self.label}' falló: {exc}") from exc

        return self._parse(data)

    def _parse(self, data: dict[str, Any]) -> ModelResponse:
        choices = data.get("choices") or []
        if not choices:
            raise ModelError(f"Respuesta sin 'choices' del proveedor '{self.label}': {data}")
        message = choices[0].get("message") or {}

        tool_calls: list[ToolCall] = []
        for raw in message.get("tool_calls") or []:
            function = raw.get("function") or {}
            arguments = function.get("arguments")
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments) if arguments.strip() else {}
                except json.JSONDecodeError:
                    arguments = {"_raw": arguments}
            tool_calls.append(
                ToolCall(
                    id=raw.get("id") or f"call_{len(tool_calls)}",
                    name=function.get("name") or "",
                    arguments=arguments or {},
                )
            )

        return ModelResponse(
            content=message.get("content") or "",
            tool_calls=tool_calls,
            model=data.get("model") or self.model,
            finish_reason=choices[0].get("finish_reason"),
            usage=data.get("usage"),
        )
