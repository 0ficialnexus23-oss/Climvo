"""Pruebas de herramientas: validación, permisos, confinamiento y auditoría."""

from __future__ import annotations

from pathlib import Path

import pytest

from elielsito.audit import AuditLog
from elielsito.config import SafetyConfig
from elielsito.memory.store import MemoryStore
from elielsito.tools.base import Permission, Tool, ToolResult, ToolValidationError, validate_arguments
from elielsito.tools.filesystem import ListDirTool, ReadFileTool, WriteFileTool, resolve_safe
from elielsito.tools.memory_tools import MemorySaveTool, MemorySearchTool
from elielsito.tools.registry import ToolRegistry


# --------------------------------------------------------------- validación
def test_validacion_parametros_obligatorios():
    schema = {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}
    with pytest.raises(ToolValidationError, match="obligatorio"):
        validate_arguments(schema, {})
    validate_arguments(schema, {"path": "ok"})


def test_validacion_tipos_y_desconocidos():
    schema = {
        "type": "object",
        "properties": {"n": {"type": "integer"}, "t": {"type": "string"}},
        "required": [],
    }
    with pytest.raises(ToolValidationError, match="entero"):
        validate_arguments(schema, {"n": "no-es-entero"})
    with pytest.raises(ToolValidationError, match="desconocido"):
        validate_arguments(schema, {"otro": 1})
    with pytest.raises(ToolValidationError, match="entero"):
        validate_arguments(schema, {"n": True})


def test_validacion_enum():
    schema = {"type": "object", "properties": {"c": {"type": "string", "enum": ["a", "b"]}}}
    with pytest.raises(ToolValidationError, match="uno de"):
        validate_arguments(schema, {"c": "z"})


# ------------------------------------------------------------ confinamiento
def test_resolve_safe_dentro_y_fuera(tmp_path: Path):
    permitida = resolve_safe(str(tmp_path / "a.txt"), [tmp_path])
    assert permitida == (tmp_path / "a.txt").resolve()

    with pytest.raises(PermissionError):
        resolve_safe("/etc/passwd", [tmp_path])

    # Intento de escape con ../
    with pytest.raises(PermissionError):
        resolve_safe(str(tmp_path / ".." / "afuera.txt"), [tmp_path])


# ------------------------------------------------------------- herramientas
def test_escritura_y_lectura(tmp_path: Path):
    escribir = WriteFileTool([tmp_path])
    leer = ReadFileTool([tmp_path])

    resultado = escribir.run(path=str(tmp_path / "nota.txt"), content="hola Elielsito")
    assert resultado.ok

    lectura = leer.run(path=str(tmp_path / "nota.txt"))
    assert lectura.ok
    assert "hola Elielsito" in lectura.output


def test_lectura_fuera_de_raices(tmp_path: Path):
    leer = ReadFileTool([tmp_path])
    resultado = leer.run(path="/etc/hostname")
    assert resultado.ok is False
    assert "fuera de las raíces" in (resultado.error or "")


def test_listar_directorio(tmp_path: Path):
    (tmp_path / "uno.txt").write_text("x", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    resultado = ListDirTool([tmp_path]).run(path=str(tmp_path))
    assert resultado.ok
    assert "uno.txt" in resultado.output
    assert "[dir] sub" in resultado.output


# ----------------------------------------------------------------- registro
class _EchoTool(Tool):
    name = "echo"
    description = "Devuelve el texto recibido"
    permission = Permission.READ
    parameters = {
        "type": "object",
        "properties": {"texto": {"type": "string"}},
        "required": ["texto"],
    }

    def run(self, texto: str, **_) -> ToolResult:
        return ToolResult.success(texto)


class _PeligrosaTool(Tool):
    name = "borrar_todo"
    description = "Herramienta destructiva de prueba"
    permission = Permission.DANGER
    parameters = {"type": "object", "properties": {}}

    def run(self, **_) -> ToolResult:
        return ToolResult.success("hecho")


def _registry(tmp_path: Path, **safety_kwargs) -> ToolRegistry:
    safety = SafetyConfig(**safety_kwargs)
    return ToolRegistry(safety=safety, audit=AuditLog(tmp_path / "audit.log"))


def test_ejecucion_correcta_y_auditoria(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.register(_EchoTool())
    resultado = registry.execute("echo", {"texto": "hola"})
    assert resultado.ok and resultado.output == "hola"
    assert any(r["event"] == "tool_run" for r in AuditLog(tmp_path / "audit.log").tail())


def test_herramienta_desconocida(tmp_path: Path):
    registry = _registry(tmp_path)
    resultado = registry.execute("no_existe", {})
    assert resultado.ok is False
    assert "No existe la herramienta" in (resultado.error or "")


def test_argumentos_invalidos_no_ejecutan(tmp_path: Path):
    registry = _registry(tmp_path)
    registry.register(_EchoTool())
    resultado = registry.execute("echo", {})
    assert resultado.ok is False
    assert "Argumentos inválidos" in (resultado.error or "")


def test_permiso_peligroso_requiere_autorizacion(tmp_path: Path):
    registry = _registry(tmp_path)  # sin callback de aprobación
    registry.register(_PeligrosaTool())
    denegado = registry.execute("borrar_todo", {})
    assert denegado.ok is False
    assert "autorización" in (denegado.error or "")

    autorizado = _registry(tmp_path)
    autorizado.approve = lambda name, perm, args: True
    autorizado.register(_PeligrosaTool())
    assert autorizado.execute("borrar_todo", {}).ok is True


def test_permiso_execute_bloqueado_por_defecto(tmp_path: Path):
    class _ShellTool(Tool):
        name = "run_shell"
        description = "ejecuta comandos"
        permission = Permission.EXECUTE
        parameters = {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}

        def run(self, cmd: str, **_) -> ToolResult:
            return ToolResult.success(cmd)

    registry = _registry(tmp_path, allow_shell=False, require_approval=[])
    registry.register(_ShellTool())
    resultado = registry.execute("run_shell", {"cmd": "ls"})
    assert resultado.ok is False
    assert "desactivadas" in (resultado.error or "")


def test_herramientas_de_memoria(tmp_path: Path):
    store = MemoryStore(tmp_path / "memoria.db")
    guardar = MemorySaveTool(store)
    buscar = MemorySearchTool(store)

    assert guardar.run(content="Elielsito se escribe con dos i", category="project").ok
    resultado = buscar.run(query="Elielsito")
    assert resultado.ok
    assert "dos i" in resultado.output
    store.close()
