#!/usr/bin/env python3
"""Configura Elielsito para usar Ollama: modelo local, gratis y sin claves.

Uso:
    python scripts/configurar_ollama.py                # detecta RAM y recomienda
    python scripts/configurar_ollama.py --model qwen2.5:7b
    python scripts/configurar_ollama.py --base-url http://localhost:11434/v1
    python scripts/configurar_ollama.py --check         # comprueba si Ollama responde

No instala nada: solo escribe la configuración y te indica los pasos que faltan.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# Permite ejecutar el script desde la raíz del proyecto sin instalar el paquete.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from elielsito.config import Config  # noqa: E402

DEFAULT_BASE_URL = "http://localhost:11434/v1"


def total_ram_gb() -> float:
    """Devuelve la RAM total en GB, o 0.0 si no se puede detectar."""
    system = platform.system()
    try:
        if system == "Linux":
            with open("/proc/meminfo", encoding="utf-8") as handle:
                for line in handle:
                    if line.startswith("MemTotal:"):
                        return int(line.split()[1]) / 1024 / 1024
        elif system == "Darwin":
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)
            return int(out.strip()) / 1024**3
        elif system == "Windows":
            import ctypes

            class _MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = _MemoryStatus()
            status.dwLength = ctypes.sizeof(status)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return status.ullTotalPhys / 1024**3
    except Exception:
        return 0.0
    return 0.0


def recomendar_modelo(ram_gb: float) -> tuple[str, str]:
    if ram_gb <= 0:
        return "qwen2.5:3b", "No pude detectar la RAM; empiezo por el modelo más ligero."
    if ram_gb < 8:
        return "qwen2.5:3b", f"{ram_gb:.1f} GB de RAM: modelo de 3B (ligero)."
    if ram_gb < 16:
        return "qwen2.5:7b", f"{ram_gb:.1f} GB de RAM: modelo de 7B (buen equilibrio)."
    if ram_gb < 32:
        return "qwen2.5:14b", f"{ram_gb:.1f} GB de RAM: modelo de 14B (más capacidad)."
    return "qwen2.5:32b", f"{ram_gb:.1f} GB de RAM: modelo de 32B (máxima calidad local)."


def comprobar_ollama(base_url: str) -> tuple[bool, str]:
    """Comprueba si el servidor Ollama responde en /api/tags."""
    host = base_url.replace("/v1", "").rstrip("/")
    url = f"{host}/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
        modelos = [m.get("name", "?") for m in data.get("models", [])]
        if modelos:
            return True, "Ollama responde. Modelos instalados: " + ", ".join(modelos)
        return True, "Ollama responde, pero no hay modelos descargados todavía."
    except Exception as exc:  # noqa: BLE001
        return False, f"No pude conectar con Ollama en {url}: {exc}"


def instrucciones(modelo: str, sistema: str) -> str:
    if sistema == "Windows":
        instalar = "Descarga el instalador desde https://ollama.com/download y ejecútalo."
    elif sistema == "Darwin":
        instalar = "Instala con:  brew install ollama   (o descarga https://ollama.com/download)"
    else:
        instalar = "Instala con:  curl -fsSL https://ollama.com/install.sh | sh"

    return f"""
Pasos que faltan en TU equipo (una sola vez):

  1) Instalar Ollama
     {instalar}

  2) Descargar el modelo (2–5 GB)
     ollama pull {modelo}

  3) Arrancar el servidor (suele quedar en segundo plano)
     ollama serve

  4) Comprobar que Elielsito lo ve
     python scripts/configurar_ollama.py --check
     elielsito doctor
     elielsito chat -m "Hola Elielsito"

Nota: Ollama escucha en http://localhost:11434 y expone una API compatible
con OpenAI en /v1. Por eso Elielsito no necesita ningún cambio de código.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Configura Elielsito para usar Ollama")
    parser.add_argument("--model", help="Modelo a usar (por ejemplo qwen2.5:7b)")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="URL base compatible con OpenAI")
    parser.add_argument("--check", action="store_true", help="Solo comprueba la conexión con Ollama")
    parser.add_argument("--config", help="Ruta alternativa del archivo de configuración")
    args = parser.parse_args()

    if args.check:
        ok, detalle = comprobar_ollama(args.base_url)
        print(("OK  " if ok else "FALLO ") + detalle)
        return 0 if ok else 1

    ram = total_ram_gb()
    sugerido, motivo = recomendar_modelo(ram)
    modelo = args.model or sugerido
    sistema = platform.system()

    print("=" * 62)
    print("  Configuración de Elielsito con Ollama (modelo local, gratis)")
    print("=" * 62)
    print(f"  Sistema detectado : {sistema} {platform.release()}")
    print(f"  RAM detectada     : {ram:.1f} GB" if ram else "  RAM detectada     : no disponible")
    print(f"  Modelo            : {modelo}   ({motivo})")
    print(f"  Servidor          : {args.base_url}")

    config = Config.load(Path(args.config) if args.config else None)
    config.model.provider = "ollama"
    config.model.name = modelo
    config.model.base_url = args.base_url
    config.validate()
    config.ensure_dirs()
    destino = config.save(Path(args.config) if args.config else None)

    print(f"\n  Configuración guardada en: {destino}")

    ok, detalle = comprobar_ollama(args.base_url)
    print(f"  Conexión con Ollama: {'OK' if ok else 'todavía no'} — {detalle}")

    print(instrucciones(modelo, sistema))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
