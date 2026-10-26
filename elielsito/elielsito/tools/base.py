"""Contratos de herramientas.

Cada herramienta declara:
- nombre y descripción (lo que ve el modelo),
- esquema JSON de parámetros (para validar y para el proveedor),
- nivel de permiso (lo que ve el sistema de seguridad).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Permission(str, Enum):
    READ = "read"          # solo lectura
    WRITE = "write"        # modifica archivos o memoria
    NETWORK = "network"    # accede a la red
    EXECUTE = "execute"    # ejecuta comandos o programas
    DANGER = "danger"      # irreversible o de alto impacto


class ToolValidationError(ValueError):
    """Los argumentos no cumplen el esquema declarado."""


@dataclass
class ToolResult:
    ok: bool
    output: str = ""
    error: str | None = None
    data: Any = None

    @classmethod
    def success(cls, output: str, data: Any = None) -> "ToolResult":
        return cls(ok=True, output=output, data=data)

    @classmethod
    def failure(cls, error: str, data: Any = None) -> "ToolResult":
        return cls(ok=False, output="", error=error, data=data)

    def as_text(self) -> str:
        return self.output if self.ok else f"ERROR: {self.error}"


_TYPE_MAP: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}

_TYPE_NAMES = {
    "string": "texto",
    "integer": "entero",
    "number": "número",
    "boolean": "booleano",
    "array": "lista",
    "object": "objeto",
}


def validate_arguments(schema: dict[str, Any], arguments: dict[str, Any]) -> None:
    """Validador mínimo de un subconjunto de JSON Schema."""
    if not isinstance(arguments, dict):
        raise ToolValidationError("Los argumentos deben ser un objeto JSON.")

    properties: dict[str, Any] = schema.get("properties", {}) or {}
    errors: list[str] = []

    for required in schema.get("required", []) or []:
        if required not in arguments:
            errors.append(f"falta el parámetro obligatorio '{required}'")

    for key, value in arguments.items():
        spec = properties.get(key)
        if spec is None:
            errors.append(f"parámetro desconocido '{key}'")
            continue
        expected = spec.get("type")
        types = _TYPE_MAP.get(expected or "")
        if types is None:
            continue
        if expected == "integer" and isinstance(value, bool):
            errors.append(f"'{key}' debe ser entero")
            continue
        if not isinstance(value, types):
            errors.append(
                f"'{key}' debe ser de tipo {_TYPE_NAMES.get(expected or '', expected)}"
            )
            continue
        if "enum" in spec and value not in spec["enum"]:
            errors.append(f"'{key}' debe ser uno de {spec['enum']}")

    if errors:
        raise ToolValidationError("; ".join(errors))


class Tool(ABC):
    name: str = ""
    description: str = ""
    permission: Permission = Permission.READ
    parameters: dict[str, Any] = {"type": "object", "properties": {}}

    def schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    def validate(self, arguments: dict[str, Any]) -> None:
        validate_arguments(self.parameters, arguments)

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        """Ejecuta la herramienta. No debe lanzar excepciones: devuelve ToolResult."""
