"""Herramientas que permiten a Elielsito usar su propia memoria."""

from __future__ import annotations

from typing import Any

from ..memory.store import CATEGORIES, KINDS, MemoryStore
from .base import Permission, Tool, ToolResult


class MemorySaveTool(Tool):
    name = "memory_save"
    description = (
        "Guarda un dato útil en la memoria persistente. Úsalo para preferencias, "
        "decisiones de proyecto, experiencias o conocimientos. No guardes secretos."
    )
    permission = Permission.WRITE
    parameters = {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "Qué recordar (una frase clara)"},
            "category": {"type": "string", "enum": list(CATEGORIES), "description": "Tipo de memoria"},
            "kind": {"type": "string", "enum": list(KINDS), "description": "Hecho verificado o hipótesis"},
            "source": {"type": "string", "description": "De dónde salió el dato"},
        },
        "required": ["content"],
    }

    def __init__(self, store: MemoryStore):
        self.store = store

    def run(
        self,
        content: str,
        category: str = "knowledge",
        kind: str = "fact",
        source: str | None = None,
        **_: Any,
    ) -> ToolResult:
        try:
            item, created = self.store.add(
                content, category=category, kind=kind, source=source
            )
        except ValueError as exc:
            return ToolResult.failure(str(exc))
        accion = "guardado" if created else "actualizado"
        return ToolResult.success(
            f"Recuerdo {accion} (id {item.id}, categoría {item.category}).",
            data={"id": item.id, "created": created},
        )


class MemorySearchTool(Tool):
    name = "memory_search"
    description = "Busca en la memoria persistente por relevancia."
    permission = Permission.READ
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Qué buscar"},
            "category": {"type": "string", "enum": list(CATEGORIES), "description": "Filtrar por categoría"},
            "limit": {"type": "integer", "description": "Máximo de resultados"},
        },
        "required": ["query"],
    }

    def __init__(self, store: MemoryStore):
        self.store = store

    def run(self, query: str, category: str | None = None, limit: int = 6, **_: Any) -> ToolResult:
        items = self.store.search(query, category=category, limit=int(limit or 6))
        if not items:
            return ToolResult.success("No encontré nada en la memoria para esa búsqueda.", data={"count": 0})
        text = "\n".join(f"- (id {i.id}) {i.render()}" for i in items)
        return ToolResult.success(text, data={"count": len(items)})
