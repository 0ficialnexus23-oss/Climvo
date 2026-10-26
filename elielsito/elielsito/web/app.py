"""Interfaz web local de Elielsito (FastAPI).

Reutiliza exactamente el mismo motor que la CLI: el agente, la memoria, las
herramientas y la auditoría. La web es solo otra "cara" del mismo sistema.

Seguridad:
- Escucha en 127.0.0.1 por defecto (solo tu equipo).
- Las herramientas que requieren autorización se deniegan desde la web
  (la aprobación interactiva llegará en una etapa posterior).
- Todo uso de herramientas sigue quedando registrado en la auditoría.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..audit import AuditLog
from ..config import Config
from ..core import Agent
from ..identity import IDENTITY
from ..memory.store import CATEGORIES, KINDS
from ..models.base import Message

STATIC_DIR = Path(__file__).parent / "static"


# ---------------------------------------------------------------- modelos
class HistoryItem(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(default="", max_length=8000)


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    history: list[HistoryItem] = Field(default_factory=list, max_length=40)


class MemoryIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    category: str = "knowledge"
    kind: str = "fact"
    source: str | None = Field(default=None, max_length=300)


# ------------------------------------------------------------------- app
def create_app(config: Config | None = None) -> FastAPI:
    cfg = config or Config.load()
    cfg.ensure_dirs()

    # Un solo candado para el agente y la memoria: SQLite y el bucle del agente
    # no están pensados para ejecutarse en paralelo sobre la misma conexión.
    lock = threading.RLock()
    agent = Agent(cfg, approve=lambda *_: False)
    audit = AuditLog(cfg.audit_file)

    app = FastAPI(
        title="Elielsito AI",
        version="0.3.0",
        description="Interfaz web local de Elielsito",
        docs_url=None,
        redoc_url=None,
    )

    # ------------------------------------------------------------- páginas
    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # --------------------------------------------------------------- estado
    @app.get("/api/status")
    def status() -> dict[str, Any]:
        with lock:
            stats = agent.memory.stats() if agent.memory else None
            return {
                "app": cfg.app_name,
                "identity": {"name": IDENTITY.name, "role": IDENTITY.role},
                "provider": cfg.model.provider,
                "model": cfg.model.name,
                "base_url": cfg.model.base_url,
                "shell_allowed": cfg.safety.allow_shell,
                "limits": {
                    "max_steps": cfg.safety.max_steps,
                    "max_seconds": cfg.safety.max_seconds,
                },
                "memory": stats,
                "tools": len(agent.registry.all()) if agent.registry else 0,
            }

    @app.get("/api/tools")
    def tools() -> list[dict[str, Any]]:
        with lock:
            if not agent.registry:
                return []
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "permission": tool.permission.value,
                }
                for tool in agent.registry.all()
            ]

    # ----------------------------------------------------------------- chat
    @app.post("/api/chat")
    def chat(payload: ChatIn) -> dict[str, Any]:
        history = [Message(item.role, item.content) for item in payload.history]
        with lock:
            result = agent.chat(payload.message, history=history)
        return {
            "reply": result.reply,
            "stopped_reason": result.stopped_reason,
            "model": result.model,
            "steps": result.steps,
            "tool_calls": result.tool_calls,
            "trace": result.trace,
            "usage": result.usage,
        }

    # --------------------------------------------------------------- memoria
    @app.get("/api/memory")
    def memory_list(
        q: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        with lock:
            if not agent.memory:
                return []
            limit = max(1, min(limit, 200))
            items = (
                agent.memory.search(q, category=category, limit=limit)
                if q
                else agent.memory.list(category=category, limit=limit)
            )
            return [item.to_dict() for item in items]

    @app.post("/api/memory", status_code=201)
    def memory_add(payload: MemoryIn) -> dict[str, Any]:
        if payload.category not in CATEGORIES:
            raise HTTPException(status_code=400, detail="Categoría no válida")
        if payload.kind not in KINDS:
            raise HTTPException(status_code=400, detail="Tipo no válido")
        with lock:
            if not agent.memory:
                raise HTTPException(status_code=400, detail="La memoria está desactivada")
            try:
                item, created = agent.memory.add(
                    payload.content,
                    category=payload.category,
                    kind=payload.kind,
                    source=payload.source,
                )
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return {"item": item.to_dict(), "created": created}

    @app.delete("/api/memory/{memory_id}")
    def memory_delete(memory_id: int) -> dict[str, bool]:
        with lock:
            if not agent.memory:
                raise HTTPException(status_code=400, detail="La memoria está desactivada")
            return {"deleted": agent.memory.delete(memory_id)}

    # -------------------------------------------------------------- auditoría
    @app.get("/api/audit")
    def audit_tail(limit: int = 50) -> list[dict[str, Any]]:
        return audit.tail(limit=max(1, min(limit, 200)))

    # ---------------------------------------------------------------- estáticos
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


# Instancia para `uvicorn elielsito.web.app:app`
app = create_app()
