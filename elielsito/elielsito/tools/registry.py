"""Registro y ejecución controlada de herramientas.

Toda ejecución pasa por aquí: valida argumentos, comprueba permisos, pide
autorización cuando corresponde y deja constancia en el registro de auditoría.
"""

from __future__ import annotations

import time
from typing import Any, Callable

from ..audit import AuditLog
from ..config import SafetyConfig
from .base import Permission, Tool, ToolResult, ToolValidationError

# Firma del callback de aprobación: recibe (nombre, permiso, argumentos) y
# devuelve True si el usuario autoriza la operación.
ApprovalCallback = Callable[[str, str, dict[str, Any]], bool]


class ToolRegistry:
    def __init__(
        self,
        *,
        safety: SafetyConfig,
        audit: AuditLog,
        approve: ApprovalCallback | None = None,
    ):
        self.safety = safety
        self.audit = audit
        self.approve = approve
        self._tools: dict[str, Tool] = {}

    # ------------------------------------------------------------- registro
    def register(self, tool: Tool) -> None:
        if not tool.name:
            raise ValueError("La herramienta no tiene nombre.")
        if tool.name in self._tools:
            raise ValueError(f"Ya existe una herramienta llamada '{tool.name}'.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return sorted(self._tools)

    def all(self) -> list[Tool]:
        return [self._tools[name] for name in self.names()]

    def schemas(self) -> list[dict[str, Any]]:
        return [tool.schema() for tool in self.all()]

    def summary(self) -> str:
        lines = []
        for tool in self.all():
            lines.append(f"- {tool.name} [{tool.permission.value}]: {tool.description}")
        return "\n".join(lines) if lines else "(no hay herramientas registradas)"

    # ------------------------------------------------------------ ejecución
    def execute(self, name: str, arguments: dict[str, Any] | None = None) -> ToolResult:
        arguments = arguments or {}
        started = time.time()

        tool = self._tools.get(name)
        if tool is None:
            return ToolResult.failure(
                f"No existe la herramienta '{name}'. Disponibles: {', '.join(self.names()) or 'ninguna'}."
            )

        try:
            tool.validate(arguments)
        except ToolValidationError as exc:
            self._audit("tool_rejected", tool=name, reason="validacion", detail=str(exc), arguments=arguments)
            return ToolResult.failure(f"Argumentos inválidos para '{name}': {exc}")

        permission = tool.permission
        if permission == Permission.EXECUTE and not self.safety.allow_shell:
            self._audit("tool_blocked", tool=name, reason="shell_desactivado", arguments=arguments)
            return ToolResult.failure(
                "Las herramientas de ejecución están desactivadas. "
                "Actívalas con ELELSITO_ALLOW_SHELL=1 si sabes lo que haces."
            )

        if permission.value in (self.safety.require_approval or []):
            if self.approve is None or not self.approve(name, permission.value, arguments):
                self._audit("tool_denied", tool=name, reason="sin_autorizacion", arguments=arguments)
                return ToolResult.failure(
                    f"La herramienta '{name}' requiere tu autorización explícita y no se concedió."
                )

        try:
            result = tool.run(**arguments)
        except Exception as exc:  # noqa: BLE001 - una herramienta no debe tumbar el agente
            self._audit(
                "tool_error",
                tool=name,
                arguments=arguments,
                error=str(exc),
                duration_ms=int((time.time() - started) * 1000),
            )
            return ToolResult.failure(f"La herramienta '{name}' falló: {exc}")

        self._audit(
            "tool_run",
            tool=name,
            permission=permission.value,
            arguments=arguments,
            ok=result.ok,
            duration_ms=int((time.time() - started) * 1000),
        )
        return result

    # ------------------------------------------------------------- auditoría
    def _audit(self, event: str, **fields: Any) -> None:
        try:
            self.audit.log(event, **fields)
        except Exception:  # la auditoría nunca debe romper la ejecución
            pass
