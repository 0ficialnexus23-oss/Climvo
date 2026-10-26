"""Interfaz de línea de comandos de Elielsito.

Comandos:
    elielsito doctor                 Revisa entorno y configuración.
    elielsito chat                   Conversación interactiva.
    elielsito chat -m "texto"        Un solo mensaje.
    elielsito tools                  Lista las herramientas.
    elielsito memory list|search|add|delete|export|stats
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from pathlib import Path

from .config import Config
from .core import Agent
from .identity import IDENTITY
from .memory.store import CATEGORIES, KINDS, MemoryStore
from .models.factory import build_adapter

BANNER = r"""
   ___ _ _      _ _
  | __| (_) ___| (_)___ ___
  | _|| | |/ -_) | (_-</ _ \
  |___|_|_|\___|_|_/__/\___/   AI
"""


def _approval_prompt(name: str, permission: str, arguments: dict) -> bool:
    print(f"\n⚠️  Elielsito quiere usar '{name}' (permiso: {permission})")
    print(f"   Argumentos: {json.dumps(arguments, ensure_ascii=False)}")
    try:
        answer = input("   ¿Autorizas esta operación? [s/N]: ").strip().lower()
    except EOFError:
        return False
    return answer in {"s", "si", "sí", "y", "yes"}


def _load_config(args: argparse.Namespace) -> Config:
    config = Config.load(Path(args.config) if args.config else None)
    config.ensure_dirs()
    return config


# --------------------------------------------------------------------- doctor
def cmd_doctor(args: argparse.Namespace) -> int:
    config = _load_config(args)
    print(BANNER)
    print(f"Identidad: {IDENTITY.name} ({IDENTITY.full_name})")
    print(f"Versión de Python: {platform.python_version()}")
    print(f"Sistema: {platform.system()} {platform.release()}")
    print(f"Carpeta de datos: {config.data_path}")
    print(f"Archivo de configuración: {config.config_file} {'(existe)' if config.config_file.exists() else '(no existe todavía)'}")
    print(f"Memoria: {'activada' if config.memory.enabled else 'desactivada'} -> {config.memory_db}")
    print(f"Proveedor de modelo: {config.model.provider} / {config.model.name}")
    print(f"Shell permitido: {config.safety.allow_shell}")
    print(f"Raíces permitidas: {', '.join(str(r) for r in config.allowed_roots())}")
    print(f"Límites: {config.safety.max_steps} pasos, {config.safety.max_seconds}s")

    ok = True
    try:
        adapter = build_adapter(config)
        reachable, detail = adapter.health()
        estado = "OK" if reachable else "AVISO"
        print(f"Adaptador de modelo: {estado} ({adapter.model}) — {detail}")
        ok = ok and reachable
    except Exception as exc:  # noqa: BLE001
        print(f"Adaptador de modelo: ERROR — {exc}")
        ok = False

    if config.memory.enabled:
        try:
            store = MemoryStore(config.memory_db)
            stats = store.stats()
            print(f"Memoria: OK (FTS5={'sí' if store.has_fts else 'no'}) — {stats}")
            store.close()
        except Exception as exc:  # noqa: BLE001
            print(f"Memoria: ERROR — {exc}")
            ok = False

    print(f"ffmpeg (para voz futura): {'disponible' if shutil.which('ffmpeg') else 'no disponible'}")
    return 0 if ok else 1


# ----------------------------------------------------------------------- chat
def cmd_chat(args: argparse.Namespace) -> int:
    config = _load_config(args)
    agent = Agent(config, approve=_approval_prompt)

    if args.message:
        result = agent.chat(args.message)
        print(result.reply)
        if args.verbose and result.trace:
            print("\n--- herramientas usadas ---")
            for entry in result.trace:
                print(f"  [{entry['step']}] {entry['tool']}({entry['arguments']}) -> {entry['result'][:160]}")
        agent.close()
        return 0

    print(BANNER)
    print(f"{IDENTITY.name}: Aquí estoy, {IDENTITY.user_title}. ¿Qué vamos a hacer hoy?")
    print("(escribe 'salir' para terminar)\n")
    history = []
    try:
        while True:
            try:
                entry = input("tú › ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if entry.lower() in {"salir", "exit", "quit"}:
                break
            if not entry:
                continue
            result = agent.chat(entry, history=history)
            print(f"\n{IDENTITY.name} › {result.reply}\n")
            if args.verbose and result.trace:
                for item in result.trace:
                    print(f"   · {item['tool']} -> {item['result'][:120]}")
            history.append({"role": "user", "content": entry})  # type: ignore[arg-type]
    finally:
        agent.close()
    return 0


# ---------------------------------------------------------------------- tools
def cmd_tools(args: argparse.Namespace) -> int:
    config = _load_config(args)
    agent = Agent(config, use_memory=config.memory.enabled)
    print(f"Herramientas registradas ({len(agent.registry.all()) if agent.registry else 0}):\n")
    if agent.registry:
        for tool in agent.registry.all():
            print(f"  • {tool.name} [{tool.permission.value}]")
            print(f"      {tool.description}")
    agent.close()
    return 0


# --------------------------------------------------------------------- memory
def cmd_memory(args: argparse.Namespace) -> int:
    config = _load_config(args)
    store = MemoryStore(config.memory_db)
    try:
        action = args.action
        if action == "list":
            items = store.list(category=args.category, limit=args.limit)
            if not items:
                print("La memoria está vacía.")
            for item in items:
                print(f"[{item.id}] {item.render()}")
            return 0

        if action == "search":
            items = store.search(args.query, category=args.category, limit=args.limit)
            if not items:
                print("Sin resultados.")
            for item in items:
                print(f"[{item.id}] {item.render()}")
            return 0

        if action == "add":
            item, created = store.add(
                args.content, category=args.category, kind=args.kind, source=args.source
            )
            print(f"{'Guardado' if created else 'Actualizado'} (id {item.id}).")
            return 0

        if action == "delete":
            if args.id:
                print("Eliminado." if store.delete(args.id) else "No existía ese id.")
            elif args.query:
                print(f"Eliminados {store.delete_matching(args.query, category=args.category)} recuerdos.")
            else:
                print("Indica --id o --query.")
                return 2
            return 0

        if action == "stats":
            print(json.dumps(store.stats(), ensure_ascii=False, indent=2))
            return 0

        if action == "export":
            target = Path(args.output) if args.output else config.data_path / "memory-export.json"
            store.export_json(target)
            print(f"Memoria exportada a {target}")
            return 0

        print(f"Acción desconocida: {action}")
        return 2
    finally:
        store.close()


# ------------------------------------------------------------------------ web
def cmd_web(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:
        print('Falta uvicorn. Instala con:  pip install -e ".[web]"')
        return 1

    from .web.app import create_app

    config = _load_config(args)
    if args.host not in {"127.0.0.1", "localhost", "::1"}:
        print("AVISO: estás exponiendo Elielsito fuera de tu equipo.")

    app = create_app(config)
    print(f"Elielsito web: http://{args.host}:{args.port}")
    print("Pulsa Ctrl+C para detener.")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="elielsito", description="Asistente personal Elielsito AI")
    parser.add_argument("--config", help="Ruta alternativa del archivo de configuración")
    sub = parser.add_subparsers(dest="command", required=True)

    p_doctor = sub.add_parser("doctor", help="Revisa entorno y configuración")
    p_doctor.set_defaults(func=cmd_doctor)

    p_chat = sub.add_parser("chat", help="Conversa con Elielsito")
    p_chat.add_argument("-m", "--message", help="Un solo mensaje y termina")
    p_chat.add_argument("-v", "--verbose", action="store_true", help="Muestra las herramientas usadas")
    p_chat.set_defaults(func=cmd_chat)

    p_tools = sub.add_parser("tools", help="Lista las herramientas")
    p_tools.set_defaults(func=cmd_tools)

    p_web = sub.add_parser("web", help="Abre la interfaz web local")
    p_web.add_argument("--host", default="127.0.0.1", help="Interfaz de red (por defecto solo local)")
    p_web.add_argument("--port", type=int, default=8765, help="Puerto (por defecto 8765)")
    p_web.set_defaults(func=cmd_web)

    p_mem = sub.add_parser("memory", help="Gestiona la memoria")
    mem_sub = p_mem.add_subparsers(dest="action", required=True)

    m_list = mem_sub.add_parser("list", help="Lista recuerdos")
    m_list.add_argument("--category", choices=CATEGORIES)
    m_list.add_argument("--limit", type=int, default=50)
    m_list.set_defaults(func=cmd_memory)

    m_search = mem_sub.add_parser("search", help="Busca recuerdos")
    m_search.add_argument("query")
    m_search.add_argument("--category", choices=CATEGORIES)
    m_search.add_argument("--limit", type=int, default=10)
    m_search.set_defaults(func=cmd_memory)

    m_add = mem_sub.add_parser("add", help="Añade un recuerdo")
    m_add.add_argument("content")
    m_add.add_argument("--category", choices=CATEGORIES, default="knowledge")
    m_add.add_argument("--kind", choices=KINDS, default="fact")
    m_add.add_argument("--source")
    m_add.set_defaults(func=cmd_memory)

    m_del = mem_sub.add_parser("delete", help="Elimina recuerdos")
    m_del.add_argument("--id", type=int)
    m_del.add_argument("--query")
    m_del.add_argument("--category", choices=CATEGORIES)
    m_del.set_defaults(func=cmd_memory)

    m_stats = mem_sub.add_parser("stats", help="Estadísticas de la memoria")
    m_stats.set_defaults(func=cmd_memory)

    m_exp = mem_sub.add_parser("export", help="Exporta la memoria a JSON")
    m_exp.add_argument("--output")
    m_exp.set_defaults(func=cmd_memory)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrumpido.")
        return 130
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
