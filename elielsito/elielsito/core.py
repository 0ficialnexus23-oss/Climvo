"""Núcleo de Elielsito: el bucle que conversa, usa herramientas y se detiene.

Garantías:
- Nunca ejecuta más de ``safety.max_steps`` pasos ni más de ``safety.max_seconds``.
- Toda llamada a herramienta pasa por el registro (permisos + auditoría).
- Un fallo del modelo o de una herramienta no tumba el proceso: se informa.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

from .audit import AuditLog
from .config import Config
from .identity import IDENTITY, Identity, build_system_prompt
from .memory.store import MemoryStore
from .models.base import Message, ModelAdapter, ModelError
from .models.factory import build_adapter
from .tools.memory_tools import MemorySaveTool, MemorySearchTool
from .tools.filesystem import ListDirTool, ReadFileTool, WriteFileTool
from .tools.registry import ApprovalCallback, ToolRegistry

StoppedReason = str  # "stop" | "max_steps" | "timeout" | "model_error" | "empty"


@dataclass
class ChatResult:
    reply: str
    stopped_reason: StoppedReason = "stop"
    model: str = ""
    steps: int = 0
    tool_calls: int = 0
    trace: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] | None = None

    @property
    def ok(self) -> bool:
        return self.stopped_reason in {"stop", "max_steps", "timeout"}


def build_registry(
    config: Config,
    memory: MemoryStore,
    audit: AuditLog,
    approve: ApprovalCallback | None = None,
) -> ToolRegistry:
    registry = ToolRegistry(safety=config.safety, audit=audit, approve=approve)
    roots = config.allowed_roots()
    registry.register(ReadFileTool(roots))
    registry.register(WriteFileTool(roots))
    registry.register(ListDirTool(roots))
    registry.register(MemorySaveTool(memory))
    registry.register(MemorySearchTool(memory))
    return registry


class Agent:
    def __init__(
        self,
        config: Config,
        *,
        adapter: ModelAdapter | None = None,
        memory: MemoryStore | None = None,
        registry: ToolRegistry | None = None,
        audit: AuditLog | None = None,
        identity: Identity | None = None,
        approve: ApprovalCallback | None = None,
        use_memory: bool = True,
    ):
        self.config = config
        self.config.ensure_dirs()
        self.audit = audit or AuditLog(config.audit_file)
        self.identity = identity or IDENTITY
        self.use_memory = use_memory and config.memory.enabled
        self.memory = memory or (MemoryStore(config.memory_db) if self.use_memory else None)
        self.adapter = adapter or build_adapter(config)
        self.registry = registry or (
            build_registry(config, self.memory, self.audit, approve) if self.memory else None
        )

    # ------------------------------------------------------------------ chat
    def chat(self, message: str, *, history: list[Message] | None = None) -> ChatResult:
        message = (message or "").strip()
        if not message:
            return ChatResult(reply="No recibí ningún mensaje.", stopped_reason="empty")

        history = list(history or [])
        self.audit.log("chat_start", model=self.adapter.model, provider=self.config.model.provider)

        memory_context = ""
        if self.memory is not None:
            try:
                memory_context = self.memory.context_for(message)
            except Exception as exc:  # la memoria no debe impedir responder
                self.audit.log("memory_error", error=str(exc))

        system_prompt = build_system_prompt(
            identity=self.identity,
            memory_context=memory_context or None,
            tools_summary=self.registry.summary() if self.registry else None,
        )
        messages: list[Message] = [Message("system", system_prompt), *history, Message("user", message)]

        started = time.time()
        trace: list[dict[str, Any]] = []
        tool_calls_made = 0

        for step in range(1, self.config.safety.max_steps + 1):
            if time.time() - started > self.config.safety.max_seconds:
                return self._finish(
                    "Me detuve: se superó el tiempo máximo de ejecución configurado.",
                    "timeout",
                    trace,
                    tool_calls_made,
                    step - 1,
                )

            tools_schema = self.registry.schemas() if self.registry else None
            try:
                response = self.adapter.complete(messages, tools=tools_schema)
            except ModelError as exc:
                self.audit.log("model_error", error=str(exc))
                return self._finish(
                    f"No pude obtener respuesta del modelo: {exc}", "model_error", trace, tool_calls_made, step
                )

            if not response.tool_calls:
                self.audit.log("chat_end", reason="stop", steps=step, tool_calls=tool_calls_made)
                return ChatResult(
                    reply=response.content or "(respuesta vacía)",
                    stopped_reason="stop",
                    model=response.model or self.adapter.model,
                    steps=step,
                    tool_calls=tool_calls_made,
                    trace=trace,
                    usage=response.usage,
                )

            messages.append(
                Message("assistant", response.content or "", tool_calls=response.tool_calls)
            )

            for call in response.tool_calls:
                tool_calls_made += 1
                if self.registry is None:
                    result_text = "ERROR: no hay herramientas disponibles."
                else:
                    result = self.registry.execute(call.name, call.arguments)
                    result_text = result.as_text()
                trace.append({"step": step, "tool": call.name, "arguments": call.arguments, "result": result_text})
                messages.append(
                    Message("tool", result_text, name=call.name, tool_call_id=call.id)
                )

        self.audit.log("chat_end", reason="max_steps", steps=self.config.safety.max_steps, tool_calls=tool_calls_made)
        return self._finish(
            "Me detuve al alcanzar el límite de pasos. Si quieres que continúe, "
            "dímelo y seguimos desde aquí.",
            "max_steps",
            trace,
            tool_calls_made,
            self.config.safety.max_steps,
        )

    def _finish(
        self,
        reply: str,
        reason: StoppedReason,
        trace: list[dict[str, Any]],
        tool_calls: int,
        steps: int,
    ) -> ChatResult:
        return ChatResult(
            reply=reply,
            stopped_reason=reason,
            model=self.adapter.model,
            steps=steps,
            tool_calls=tool_calls,
            trace=trace,
        )

    # -------------------------------------------------------------- utilidades
    def remember(
        self,
        content: str,
        *,
        category: str = "knowledge",
        kind: str = "fact",
        source: str | None = None,
    ):
        if self.memory is None:
            raise RuntimeError("La memoria está desactivada.")
        return self.memory.add(content, category=category, kind=kind, source=source)

    def close(self) -> None:
        if self.memory is not None:
            self.memory.close()
