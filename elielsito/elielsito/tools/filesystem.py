"""Herramientas de archivos, confinadas a las raíces permitidas.

Regla de seguridad central: ninguna ruta puede salir de las raíces autorizadas.
Se resuelve la ruta real (siguiendo enlaces simbólicos) y se comprueba que
sigue estando dentro.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import Permission, Tool, ToolResult

MAX_READ_BYTES = 200_000


class PathNotAllowed(PermissionError):
    pass


def resolve_safe(raw_path: str, roots: list[Path]) -> Path:
    """Devuelve la ruta resuelta si está dentro de alguna raíz permitida."""
    if not raw_path or not raw_path.strip():
        raise PathNotAllowed("La ruta está vacía.")
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = roots[0] / candidate
    try:
        resolved = candidate.resolve()
    except OSError as exc:
        raise PathNotAllowed(f"No se pudo resolver la ruta: {exc}") from exc

    for root in roots:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue
    allowed = ", ".join(str(r) for r in roots)
    raise PathNotAllowed(f"La ruta '{raw_path}' está fuera de las raíces permitidas: {allowed}")


class _BaseFsTool(Tool):
    def __init__(self, roots: list[Path]):
        self.roots = [Path(r).resolve() for r in roots]


class ReadFileTool(_BaseFsTool):
    name = "read_file"
    description = "Lee un archivo de texto y devuelve su contenido."
    permission = Permission.READ
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Ruta del archivo a leer"},
            "max_bytes": {"type": "integer", "description": "Máximo de bytes a leer"},
        },
        "required": ["path"],
    }

    def run(self, path: str, max_bytes: int = MAX_READ_BYTES, **_: Any) -> ToolResult:
        try:
            target = resolve_safe(path, self.roots)
        except PathNotAllowed as exc:
            return ToolResult.failure(str(exc))
        if not target.exists():
            return ToolResult.failure(f"No existe el archivo: {target}")
        if not target.is_file():
            return ToolResult.failure(f"La ruta no es un archivo: {target}")
        limit = min(int(max_bytes or MAX_READ_BYTES), MAX_READ_BYTES)
        try:
            data = target.read_bytes()[:limit]
        except OSError as exc:
            return ToolResult.failure(f"No se pudo leer el archivo: {exc}")
        text = data.decode("utf-8", "replace")
        truncated = target.stat().st_size > limit
        suffix = "\n… (contenido truncado)" if truncated else ""
        return ToolResult.success(text + suffix, data={"path": str(target), "truncated": truncated})


class WriteFileTool(_BaseFsTool):
    name = "write_file"
    description = "Crea o sobrescribe un archivo de texto."
    permission = Permission.WRITE
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Ruta del archivo a escribir"},
            "content": {"type": "string", "description": "Contenido a escribir"},
        },
        "required": ["path", "content"],
    }

    def run(self, path: str, content: str, **_: Any) -> ToolResult:
        try:
            target = resolve_safe(path, self.roots)
        except PathNotAllowed as exc:
            return ToolResult.failure(str(exc))
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        except OSError as exc:
            return ToolResult.failure(f"No se pudo escribir el archivo: {exc}")
        return ToolResult.success(
            f"Archivo escrito: {target} ({len(content)} caracteres)",
            data={"path": str(target), "bytes": len(content.encode('utf-8'))},
        )


class ListDirTool(_BaseFsTool):
    name = "list_dir"
    description = "Lista el contenido de un directorio."
    permission = Permission.READ
    parameters = {
        "type": "object",
        "properties": {"path": {"type": "string", "description": "Ruta del directorio"}},
        "required": ["path"],
    }

    def run(self, path: str, **_: Any) -> ToolResult:
        try:
            target = resolve_safe(path, self.roots)
        except PathNotAllowed as exc:
            return ToolResult.failure(str(exc))
        if not target.exists():
            return ToolResult.failure(f"No existe el directorio: {target}")
        if not target.is_dir():
            return ToolResult.failure(f"La ruta no es un directorio: {target}")
        try:
            entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except OSError as exc:
            return ToolResult.failure(f"No se pudo listar el directorio: {exc}")
        lines = [f"{'[dir]' if e.is_dir() else '[file]'} {e.name}" for e in entries]
        return ToolResult.success("\n".join(lines) or "(directorio vacío)", data={"count": len(entries)})
