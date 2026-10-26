#!/usr/bin/env python3
"""Verifica que Ollama y Elielsito estén correctamente conectados.

Comprueba, en orden:
  1. Que la configuración de Elielsito apunte a Ollama.
  2. Que el servidor de Ollama responda.
  3. Que el modelo configurado esté descargado.
  4. Que el modelo responda de verdad (petición real).

Uso:
    python scripts/verificar_ollama.py
    python scripts/verificar_ollama.py --config /ruta/config.json
    python scripts/verificar_ollama.py --sin-prueba   # omite la petición real
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elielsito.config import Config  # noqa: E402


@dataclass
class Check:
    nombre: str
    ok: bool
    detalle: str
    pista: str = ""


def _http_json(url: str, payload: dict | None = None, timeout: int = 10) -> dict:
    datos = json.dumps(payload).encode("utf-8") if payload is not None else None
    peticion = urllib.request.Request(url, data=datos, method="POST" if datos else "GET")
    if datos:
        peticion.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
        return json.loads(respuesta.read().decode("utf-8"))


def _host(base_url: str | None) -> str:
    return (base_url or "http://localhost:11434/v1").replace("/v1", "").rstrip("/")


def verificar(config: Config, *, prueba_real: bool = True) -> list[Check]:
    checks: list[Check] = []

    # 1. Configuración
    es_ollama = config.model.provider == "ollama"
    checks.append(
        Check(
            "Configuración apunta a Ollama",
            es_ollama,
            f"provider = {config.model.provider}, modelo = {config.model.name}",
            "" if es_ollama else "Ejecuta: python scripts/configurar_ollama.py",
        )
    )

    # 2. Servidor
    host = _host(config.model.base_url)
    modelos: list[str] = []
    try:
        datos = _http_json(f"{host}/api/tags", timeout=5)
        modelos = [m.get("name", "") for m in datos.get("models", []) if m.get("name")]
        checks.append(
            Check(
                "Servidor Ollama responde",
                True,
                f"{host} — {len(modelos)} modelo(s) instalado(s)",
            )
        )
    except Exception as exc:  # noqa: BLE001
        checks.append(
            Check(
                "Servidor Ollama responde",
                False,
                f"{host} — {exc}",
                "Arranca Ollama:  ollama serve",
            )
        )

    # 3. Modelo instalado
    modelo = config.model.name
    instalado = any(m == modelo or m.split(":")[0] == modelo.split(":")[0] for m in modelos)
    checks.append(
        Check(
            f"Modelo '{modelo}' descargado",
            instalado,
            "sí" if instalado else "no aparece en la lista",
            "" if instalado else f"Descárgalo:  ollama pull {modelo}",
        )
    )

    # 4. Respuesta real
    if prueba_real and instalado:
        try:
            datos = _http_json(
                f"{config.model.base_url or 'http://localhost:11434/v1'}/chat/completions",
                {
                    "model": modelo,
                    "messages": [{"role": "user", "content": "Responde únicamente: OK"}],
                    "max_tokens": 8,
                    "temperature": 0,
                },
                timeout=120,
            )
            contenido = (datos.get("choices") or [{}])[0].get("message", {}).get("content", "")
            checks.append(
                Check("Respuesta real del modelo", True, repr(contenido.strip()[:60]))
            )
        except Exception as exc:  # noqa: BLE001
            checks.append(
                Check(
                    "Respuesta real del modelo",
                    False,
                    str(exc),
                    "Revisa que el modelo esté completo y que haya RAM suficiente.",
                )
            )
    elif prueba_real:
        checks.append(
            Check(
                "Respuesta real del modelo",
                False,
                "omitida hasta que los pasos anteriores estén en verde",
            )
        )

    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica la conexión de Elielsito con Ollama")
    parser.add_argument("--config", help="Ruta alternativa del archivo de configuración")
    parser.add_argument("--sin-prueba", action="store_true", help="No hace la petición real al modelo")
    args = parser.parse_args()

    config = Config.load(Path(args.config) if args.config else None)
    checks = verificar(config, prueba_real=not args.sin_prueba)

    print("=" * 64)
    print("  Verificación de Elielsito + Ollama")
    print("=" * 64)
    for check in checks:
        marca = "OK   " if check.ok else "FALLA"
        print(f"  [{marca}] {check.nombre}")
        print(f"          {check.detalle}")
        if not check.ok and check.pista:
            print(f"          → {check.pista}")
    print("=" * 64)

    fallos = [c for c in checks if not c.ok]
    if fallos:
        print(f"  Quedan {len(fallos)} paso(s) pendiente(s). Sigue las pistas de arriba.")
        return 1
    print("  Todo listo. Prueba:  elielsito chat -m \"Hola Elielsito\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
