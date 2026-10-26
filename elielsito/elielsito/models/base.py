"""Contratos de los adaptadores de modelo.

Cualquier proveedor (API o local) implementa ``ModelAdapter``. El resto del
sistema solo conoce estas estructuras, de modo que cambiar de modelo no obliga
a tocar la memoria, las herramientas ni el planificador.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Literal

Role = Literal["system", "user", "assistant", "tool"]


class ModelError(RuntimeError):
    """Fallo al comunicarse con el proveedor del modelo."""


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    role: Role
    content: str = ""
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None

    def to_openai(self) -> dict[str, Any]:
        """Formato de OpenAI y de los servidores compatibles (Ollama, LM Studio)."""
        payload: dict[str, Any] = {"role": self.role, "content": self.content or ""}
        if self.name:
            payload["name"] = self.name
        if self.tool_call_id:
            payload["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            payload["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": _json_dumps(call.arguments),
                    },
                }
                for call in self.tool_calls
            ]
        return payload


@dataclass
class ModelResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    model: str = ""
    finish_reason: str | None = None
    usage: dict[str, Any] | None = None

    @property
    def wants_tools(self) -> bool:
        return bool(self.tool_calls)


def _json_dumps(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)


class ModelAdapter(ABC):
    """Interfaz común de todos los proveedores de modelo."""

    name: str = "base"
    model: str = ""

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        """Devuelve la siguiente respuesta del modelo."""

    def health(self) -> tuple[bool, str]:
        """Comprobación ligera de disponibilidad. No gasta tokens si se evita."""
        return True, "sin comprobación específica"
