"""Registro de auditoría: cada acción relevante queda registrada en JSONL.

JSONL (una línea JSON por evento) permite añadir sin reescribir el archivo y
recuperarse de una línea corrupta sin perder el resto.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuditLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, **fields: Any) -> dict:
        record = {"ts": _now(), "event": event, **fields}
        line = json.dumps(record, ensure_ascii=False, default=str)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
        return record

    def tail(self, limit: int = 50) -> list[dict]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        records: list[dict] = []
        for line in lines[-limit:]:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                # Una línea corrupta no debe tumbar la lectura del resto.
                records.append({"event": "_linea_corrupta", "raw": line[:200]})
        return records
