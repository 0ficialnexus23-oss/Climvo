"""Memoria persistente de Elielsito sobre SQLite.

Diseño:
- Una sola tabla ``memories`` con categoría, tipo (hecho/hipótesis), fuente,
  confianza, etiquetas y marcas de tiempo.
- Índice FTS5 para búsqueda por relevancia; si el SQLite del sistema no trae
  FTS5, se degrada automáticamente a búsqueda por ``LIKE`` sin fallar.
- Deduplicación por hash de (categoría + contenido normalizado).
- Exportación y borrado explícitos.
- **Nunca** se guardan secretos: el agente llama a ``looks_secret`` antes de
  almacenar y la memoria rechaza el contenido sospechoso.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

CATEGORIES = ("personal", "project", "experience", "knowledge", "operational")
KINDS = ("fact", "hypothesis")

_SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9\-_]{16,}\b"),          # claves estilo OpenAI
    re.compile(r"\bsk-ant-[A-Za-z0-9\-_]{16,}\b"),   # Anthropic
    re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}\b"),      # Google
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),   # GitHub
    re.compile(r"(?i)\b(api[_\- ]?key|token|password|contrasena|contraseña)\b\s*[:=]\s*\S+"),
)


def looks_secret(text: str) -> bool:
    """Heurística para no almacenar credenciales en la memoria."""
    return any(pattern.search(text) for pattern in _SECRET_PATTERNS)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _hash(category: str, content: str) -> str:
    raw = f"{category}::{_normalize(content)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class MemoryItem:
    id: int
    category: str
    content: str
    kind: str
    source: str | None
    confidence: float | None
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category,
            "content": self.content,
            "kind": self.kind,
            "source": self.source,
            "confidence": self.confidence,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def render(self) -> str:
        marca = "HECHO" if self.kind == "fact" else "HIPÓTESIS"
        fuente = f" · fuente: {self.source}" if self.source else ""
        return f"[{self.category}/{marca}] {self.content}{fuente}"


class MemoryStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._fts = False
        self._init_schema()

    # ------------------------------------------------------------- esquema
    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category    TEXT NOT NULL,
                content     TEXT NOT NULL,
                kind        TEXT NOT NULL DEFAULT 'fact',
                source      TEXT,
                confidence  REAL,
                tags        TEXT NOT NULL DEFAULT '',
                hash        TEXT NOT NULL UNIQUE,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
            """
        )
        try:
            self._conn.executescript(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
                    USING fts5(content, tags, content='memories', content_rowid='id');
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, content, tags)
                    VALUES (new.id, new.content, new.tags);
                END;
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content, tags)
                    VALUES ('delete', old.id, old.content, old.tags);
                END;
                CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content, tags)
                    VALUES ('delete', old.id, old.content, old.tags);
                    INSERT INTO memories_fts(rowid, content, tags)
                    VALUES (new.id, new.content, new.tags);
                END;
                """
            )
            self._fts = True
        except sqlite3.OperationalError:
            # SQLite sin FTS5: se usa búsqueda LIKE.
            self._fts = False
        self._conn.commit()

    @property
    def has_fts(self) -> bool:
        return self._fts

    # -------------------------------------------------------------- escritura
    def add(
        self,
        content: str,
        *,
        category: str = "knowledge",
        kind: str = "fact",
        source: str | None = None,
        confidence: float | None = None,
        tags: Iterable[str] | None = None,
    ) -> tuple[MemoryItem, bool]:
        """Guarda un recuerdo. Devuelve (item, creado).

        Si ya existía el mismo contenido en la misma categoría, lo actualiza
        (fuente/confianza/etiquetas) y devuelve ``creado=False``.
        """
        content = (content or "").strip()
        if not content:
            raise ValueError("No se puede guardar un recuerdo vacío.")
        if category not in CATEGORIES:
            raise ValueError(f"Categoría no válida: {category!r}. Opciones: {CATEGORIES}")
        if kind not in KINDS:
            raise ValueError(f"Tipo no válido: {kind!r}. Opciones: {KINDS}")
        if looks_secret(content):
            raise ValueError(
                "El contenido parece contener un secreto (clave, token o contraseña). "
                "No se almacena en la memoria."
            )

        tag_list = sorted({t.strip() for t in (tags or []) if t and t.strip()})
        tags_str = ",".join(tag_list)
        digest = _hash(category, content)
        now = _now()

        row = self._conn.execute(
            "SELECT id FROM memories WHERE hash = ?", (digest,)
        ).fetchone()

        if row:
            self._conn.execute(
                """
                UPDATE memories
                   SET source = COALESCE(?, source),
                       confidence = COALESCE(?, confidence),
                       tags = ?,
                       updated_at = ?
                 WHERE id = ?
                """,
                (source, confidence, tags_str, now, row["id"]),
            )
            self._conn.commit()
            return self.get(int(row["id"])), False

        cursor = self._conn.execute(
            """
            INSERT INTO memories (category, content, kind, source, confidence, tags, hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (category, content, kind, source, confidence, tags_str, digest, now, now),
        )
        self._conn.commit()
        return self.get(int(cursor.lastrowid)), True

    # --------------------------------------------------------------- lectura
    def get(self, memory_id: int) -> MemoryItem:
        row = self._conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        if row is None:
            raise KeyError(f"No existe el recuerdo {memory_id}")
        return self._row_to_item(row)

    def list(self, *, category: str | None = None, limit: int = 100) -> list[MemoryItem]:
        if category:
            rows = self._conn.execute(
                "SELECT * FROM memories WHERE category = ? ORDER BY updated_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM memories ORDER BY updated_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._row_to_item(r) for r in rows]

    def search(
        self,
        query: str,
        *,
        category: str | None = None,
        limit: int = 8,
    ) -> list[MemoryItem]:
        query = (query or "").strip()
        if not query:
            return []

        rows: list[sqlite3.Row] = []
        if self._fts:
            fts_query = self._build_fts_query(query)
            if fts_query:
                try:
                    rows = self._conn.execute(
                        """
                        SELECT m.* FROM memories_fts f
                        JOIN memories m ON m.id = f.rowid
                        WHERE memories_fts MATCH ?
                        ORDER BY bm25(memories_fts)
                        LIMIT ?
                        """,
                        (fts_query, limit * 3),
                    ).fetchall()
                except sqlite3.OperationalError:
                    rows = []

        if not rows:
            like = f"%{query}%"
            rows = self._conn.execute(
                "SELECT * FROM memories WHERE content LIKE ? OR tags LIKE ? ORDER BY updated_at DESC LIMIT ?",
                (like, like, limit * 3),
            ).fetchall()

        if category:
            rows = [r for r in rows if r["category"] == category]
        return [self._row_to_item(r) for r in rows[:limit]]

    @staticmethod
    def _build_fts_query(text: str) -> str:
        tokens = re.findall(r"\w+", text.lower(), flags=re.UNICODE)
        tokens = [t for t in tokens if len(t) > 1]
        return " OR ".join(f"{t}*" for t in tokens[:8])

    def context_for(self, query: str, *, limit: int = 6) -> str:
        """Bloque de texto con la memoria relevante, listo para el mensaje de sistema."""
        items = self.search(query, limit=limit)
        if not items:
            # Si la búsqueda no encuentra nada, se aporta algo de contexto reciente
            # en lugar de dejar al agente completamente a ciegas.
            items = self.list(limit=min(limit, 3))
        if not items:
            return ""
        return "\n".join(f"- {item.render()}" for item in items)

    # -------------------------------------------------------------- borrado
    def delete(self, memory_id: int) -> bool:
        cursor = self._conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self._conn.commit()
        return cursor.rowcount > 0

    def delete_matching(self, query: str, *, category: str | None = None) -> int:
        items = self.search(query, category=category, limit=200)
        deleted = 0
        for item in items:
            if self.delete(item.id):
                deleted += 1
        return deleted

    def clear(self, *, category: str | None = None) -> int:
        if category:
            cursor = self._conn.execute("DELETE FROM memories WHERE category = ?", (category,))
        else:
            cursor = self._conn.execute("DELETE FROM memories")
        self._conn.commit()
        return cursor.rowcount

    # ------------------------------------------------------------ utilidades
    def stats(self) -> dict[str, int]:
        rows = self._conn.execute(
            "SELECT category, COUNT(*) AS n FROM memories GROUP BY category"
        ).fetchall()
        counts = {row["category"]: row["n"] for row in rows}
        counts["_total"] = sum(counts.values())
        return counts

    def export(self) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self.list(limit=100000)]

    def export_json(self, path: Path | None = None) -> str:
        payload = json.dumps(self.export(), indent=2, ensure_ascii=False)
        if path:
            Path(path).write_text(payload, encoding="utf-8")
        return payload

    def backup(self, directory: Path) -> Path:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        target = directory / f"memory-{stamp}.db"
        with sqlite3.connect(str(target)) as dest:
            self._conn.backup(dest)
        return target

    def close(self) -> None:
        self._conn.close()

    @staticmethod
    def _row_to_item(row: sqlite3.Row) -> MemoryItem:
        tags = [t for t in (row["tags"] or "").split(",") if t]
        return MemoryItem(
            id=int(row["id"]),
            category=row["category"],
            content=row["content"],
            kind=row["kind"],
            source=row["source"],
            confidence=row["confidence"],
            tags=tags,
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
