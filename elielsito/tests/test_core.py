"""Pruebas del bucle del agente."""

from __future__ import annotations

from pathlib import Path

import pytest

from elielsito.config import Config
from elielsito.core import Agent
from elielsito.models.base import Message, ModelError, ModelResponse, ToolCall
from elielsito.models.mock import MockAdapter


def _config(tmp_path: Path, **safety) -> Config:
    config = Config(data_dir=str(tmp_path / "datos"))
    config.safety.allowed_roots = [str(tmp_path)]
    for key, value in safety.items():
        setattr(config.safety, key, value)
    return config


def test_respuesta_simple(tmp_path: Path):
    agent = Agent(_config(tmp_path), adapter=MockAdapter(), approve=lambda *a: True)
    resultado = agent.chat("Hola")
    assert resultado.stopped_reason == "stop"
    assert resultado.reply
    assert resultado.tool_calls == 0
    agent.close()


def test_mensaje_vacio(tmp_path: Path):
    agent = Agent(_config(tmp_path), adapter=MockAdapter(), approve=lambda *a: True)
    resultado = agent.chat("   ")
    assert resultado.stopped_reason == "empty"
    agent.close()


def test_llamada_a_herramienta_y_continuacion(tmp_path: Path):
    script = [
        ModelResponse(
            content="",
            tool_calls=[
                ToolCall(
                    id="c1",
                    name="memory_save",
                    arguments={"content": "Al usuario le gusta el café", "category": "personal"},
                )
            ],
        ),
        ModelResponse(content="Anotado, jefe."),
    ]
    agent = Agent(_config(tmp_path), adapter=MockAdapter(script=script), approve=lambda *a: True)
    resultado = agent.chat("Recuerda que me gusta el café")

    assert resultado.reply == "Anotado, jefe."
    assert resultado.tool_calls == 1
    assert resultado.trace[0]["tool"] == "memory_save"
    assert agent.memory.search("café")
    agent.close()


def test_limite_de_pasos(tmp_path: Path):
    # El modelo pide herramientas sin parar; el agente debe cortar.
    infinito = [
        ModelResponse(
            content="",
            tool_calls=[ToolCall(id=f"c{i}", name="list_dir", arguments={"path": str(tmp_path)})],
        )
        for i in range(20)
    ]
    agent = Agent(
        _config(tmp_path, max_steps=3),
        adapter=MockAdapter(script=infinito),
        approve=lambda *a: True,
    )
    resultado = agent.chat("haz algo")
    assert resultado.stopped_reason == "max_steps"
    assert resultado.tool_calls == 3
    agent.close()


def test_error_del_modelo_no_tumba_el_agente(tmp_path: Path):
    class _Falla(MockAdapter):
        def complete(self, messages, tools=None, **kwargs):
            raise ModelError("servicio caído")

    agent = Agent(_config(tmp_path), adapter=_Falla(), approve=lambda *a: True)
    resultado = agent.chat("hola")
    assert resultado.stopped_reason == "model_error"
    assert "servicio caído" in resultado.reply
    agent.close()


def test_la_memoria_se_inyecta_en_el_prompt(tmp_path: Path):
    adapter = MockAdapter()
    agent = Agent(_config(tmp_path), adapter=adapter, approve=lambda *a: True)
    agent.remember("El usuario se llama Eliel", category="personal")
    agent.chat("¿cómo me llamo?")
    system_prompt = adapter.calls[-1][0].content
    assert "Eliel" in system_prompt
    agent.close()


def test_historial_se_respeta(tmp_path: Path):
    adapter = MockAdapter()
    agent = Agent(_config(tmp_path), adapter=adapter, approve=lambda *a: True)
    historial = [Message("user", "antes"), Message("assistant", "ok")]
    agent.chat("ahora", history=historial)
    roles = [m.role for m in adapter.calls[-1]]
    assert roles == ["system", "user", "assistant", "user"]
    agent.close()


def test_denegacion_de_autorizacion(tmp_path: Path):
    script = [
        ModelResponse(
            content="",
            tool_calls=[ToolCall(id="c1", name="write_file", arguments={"path": str(tmp_path / "x.txt"), "content": "x"})],
        ),
        ModelResponse(content="No pude escribir el archivo porque no autorizaste."),
    ]
    config = _config(tmp_path, require_approval=["write"])
    agent = Agent(config, adapter=MockAdapter(script=script), approve=lambda *a: False)
    resultado = agent.chat("escribe un archivo")

    assert "no autorizaste" in resultado.reply
    assert not (tmp_path / "x.txt").exists()
    assert "ERROR" in resultado.trace[0]["result"]
    agent.close()
