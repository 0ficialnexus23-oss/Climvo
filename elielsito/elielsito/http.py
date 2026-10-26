"""Cliente HTTP mínimo basado en la biblioteca estándar (sin dependencias)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


class HttpError(RuntimeError):
    """Error de red o de respuesta HTTP, con el cuerpo del servidor incluido."""

    def __init__(self, status: int, body: str, url: str):
        self.status = status
        self.body = body
        self.url = url
        detail = body[:400] if body else "(sin cuerpo)"
        super().__init__(f"HTTP {status} en {url}: {detail}")


def _request(url: str, *, data: bytes | None, headers: dict[str, str], timeout: int) -> str:
    request = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    for key, value in headers.items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise HttpError(exc.code, exc.read().decode("utf-8", "replace"), url) from exc
    except urllib.error.URLError as exc:
        raise HttpError(0, str(exc.reason), url) from exc


def _parse(raw: str, url: str) -> dict[str, Any]:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise HttpError(200, raw[:500], url) from exc


def post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    merged = {"Content-Type": "application/json", **(headers or {})}
    body = json.dumps(payload).encode("utf-8")
    return _parse(_request(url, data=body, headers=merged, timeout=timeout), url)


def get_json(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 30,
) -> dict[str, Any]:
    return _parse(_request(url, data=None, headers=headers or {}, timeout=timeout), url)
