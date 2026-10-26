"""Adaptador simulado: permite probar toda la arquitectura sin internet ni claves.

También sirve para las pruebas automatizadas: acepta un guion de respuestas
(``script``) que devuelve en orden, de modo que se puede simular una llamada a
herramienta y su continuación sin depender de ningún servicio externo.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .base import Message, ModelAdapter, ModelResponse, ToolCall

_TOOL_COMMAND = re.compile(r"^/tool\s+(\w+)\s*(\{.*\})?$", re.DOTALL)


class MockAdapter(ModelAdapter):
    name = "mock"

    def __init__(self, model: str = "mock-1", script: list[ModelResponse] | None = None):
        self.model = model
        self._script: list[ModelResponse] = list(script or [])
        self.calls: list[list[Message]] = []

    def complete(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> ModelResponse:
        self.calls.append(list(messages))

        if self._script:
            return self._script.pop(0)

        last = messages[-1] if messages else None

        # Si el último mensaje es el resultado de una herramienta, respondemos
        # con ese resultado en lugar de volver a pedir la misma herramienta.
        if last is not None and last.role == "tool":
            resumen = (last.content or "").strip().replace("\n", " ")
            return ModelResponse(
                content=(
                    f"[modo mock] La herramienta '{last.name or 'desconocida'}' respondió: "
                    f"{resumen[:200]}"
                ),
                model=self.model,
                finish_reason="stop",
            )

        last_user = next(
            (m for m in reversed(messages) if m.role == "user"),
            None,
        )
        text = (last_user.content if last_user else "").strip()

        # Comando de prueba: "/tool nombre {json}" fuerza una llamada a herramienta.
        match = _TOOL_COMMAND.match(text)
        if match:
            tool_name = match.group(1)
            raw_args = match.group(2) or "{}"
            try:
                arguments = json.loads(raw_args)
            except json.JSONDecodeError:
                arguments = {}
            return ModelResponse(
                content="",
                tool_calls=[ToolCall(id="mock-call-1", name=tool_name, arguments=arguments)],
                model=self.model,
                finish_reason="tool_calls",
            )

        if not text:
            reply = "Aquí estoy, jefe. ¿Qué hacemos?"
        else:
            reply = (
                f"[modo mock] Recibí tu mensaje: «{text}». "
                "No hay un modelo real conectado, así que no puedo razonar sobre "
                "él; la arquitectura sí está funcionando."
            )
        return ModelResponse(content=reply, model=self.model, finish_reason="stop")
