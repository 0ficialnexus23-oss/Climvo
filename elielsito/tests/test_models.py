"""Pruebas de los adaptadores de modelo (sin llamadas reales a servicios)."""

from __future__ import annotations

from pathlib import Path

import pytest

from elielsito.config import Config
from elielsito.models.anthropic import AnthropicAdapter
from elielsito.models.base import Message, ModelError, ModelResponse, ToolCall
from elielsito.models.factory import build_adapter
from elielsito.models.gemini import GeminiAdapter
from elielsito.models.mock import MockAdapter
from elielsito.models.openai_compatible import OpenAICompatibleAdapter


# ------------------------------------------------------------------- mock
def test_mock_responde_y_registra_llamadas():
    adapter = MockAdapter()
    respuesta = adapter.complete([Message("user", "Hola Elielsito")])
    assert "Hola Elielsito" in respuesta.content
    assert len(adapter.calls) == 1


def test_mock_sin_mensaje_saluda():
    adapter = MockAdapter()
    respuesta = adapter.complete([Message("system", "reglas")])
    assert "Aquí estoy" in respuesta.content


def test_mock_comando_de_herramienta():
    adapter = MockAdapter()
    respuesta = adapter.complete([Message("user", '/tool list_dir {"path": "/tmp"}')])
    assert respuesta.wants_tools
    assert respuesta.tool_calls[0].name == "list_dir"
    assert respuesta.tool_calls[0].arguments == {"path": "/tmp"}


def test_mock_continua_tras_resultado_de_herramienta():
    """Tras ejecutar una herramienta, el mock debe continuar en vez de repetirla."""
    adapter = MockAdapter()
    respuesta = adapter.complete(
        [
            Message("user", '/tool list_dir {"path": "/tmp"}'),
            Message("assistant", "", tool_calls=[ToolCall(id="1", name="list_dir", arguments={"path": "/tmp"})]),
            Message("tool", "[file] nota.txt", name="list_dir", tool_call_id="1"),
        ]
    )
    assert not respuesta.tool_calls
    assert "nota.txt" in respuesta.content


def test_mock_guion_se_consume_en_orden():
    adapter = MockAdapter(script=[ModelResponse(content="primero"), ModelResponse(content="segundo")])
    assert adapter.complete([Message("user", "a")]).content == "primero"
    assert adapter.complete([Message("user", "b")]).content == "segundo"


# --------------------------------------------------------- openai-compatible
def test_openai_parsea_texto_y_herramientas():
    adapter = OpenAICompatibleAdapter(model="gpt-4o-mini", api_key="test", requires_key=False)
    data = {
        "model": "gpt-4o-mini",
        "choices": [
            {
                "finish_reason": "tool_calls",
                "message": {
                    "content": "Voy a revisar.",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "function": {"name": "read_file", "arguments": '{"path": "a.txt"}'},
                        }
                    ],
                },
            }
        ],
        "usage": {"total_tokens": 12},
    }
    respuesta = adapter._parse(data)
    assert respuesta.content == "Voy a revisar."
    assert respuesta.tool_calls[0].name == "read_file"
    assert respuesta.tool_calls[0].arguments == {"path": "a.txt"}
    assert respuesta.usage == {"total_tokens": 12}


def test_openai_sin_choices_es_error():
    adapter = OpenAICompatibleAdapter(model="x", api_key="test", requires_key=False)
    with pytest.raises(ModelError, match="choices"):
        adapter._parse({"choices": []})


def test_openai_argumentos_no_json_no_rompe():
    adapter = OpenAICompatibleAdapter(model="x", api_key="test", requires_key=False)
    data = {"choices": [{"message": {"tool_calls": [{"id": "1", "function": {"name": "t", "arguments": "no-json"}}]}}]}
    respuesta = adapter._parse(data)
    assert respuesta.tool_calls[0].arguments == {"_raw": "no-json"}


def test_openai_exige_clave_cuando_corresponde():
    with pytest.raises(ModelError, match="clave"):
        OpenAICompatibleAdapter(model="gpt", api_key=None, requires_key=True)


def test_mensaje_a_formato_openai():
    mensaje = Message(
        role="assistant",
        content="hola",
        tool_calls=[ToolCall(id="1", name="t", arguments={"a": 1})],
    )
    payload = mensaje.to_openai()
    assert payload["tool_calls"][0]["function"]["name"] == "t"
    assert payload["tool_calls"][0]["function"]["arguments"] == '{"a": 1}'


# ------------------------------------------------------------------ anthropic
def test_anthropic_parsea_bloques():
    adapter = AnthropicAdapter(api_key="test")
    data = {
        "model": "claude",
        "stop_reason": "tool_use",
        "content": [
            {"type": "text", "text": "Necesito leer un archivo."},
            {"type": "tool_use", "id": "tu_1", "name": "read_file", "input": {"path": "b.txt"}},
        ],
        "usage": {"input_tokens": 5, "output_tokens": 7},
    }
    respuesta = adapter._parse(data)
    assert respuesta.content == "Necesito leer un archivo."
    assert respuesta.tool_calls[0].id == "tu_1"
    assert respuesta.tool_calls[0].arguments == {"path": "b.txt"}


def test_anthropic_exige_clave():
    with pytest.raises(ModelError, match="ANTHROPIC_API_KEY"):
        AnthropicAdapter(api_key="")


# --------------------------------------------------------------------- gemini
def test_gemini_parsea_partes():
    adapter = GeminiAdapter(api_key="test")
    data = {
        "candidates": [
            {
                "finishReason": "STOP",
                "content": {
                    "parts": [
                        {"text": "Claro."},
                        {"functionCall": {"name": "list_dir", "args": {"path": "/tmp"}}},
                    ]
                },
            }
        ],
        "usageMetadata": {"totalTokenCount": 9},
    }
    respuesta = adapter._parse(data)
    assert respuesta.content == "Claro."
    assert respuesta.tool_calls[0].name == "list_dir"
    assert respuesta.tool_calls[0].arguments == {"path": "/tmp"}


def test_gemini_exige_clave():
    with pytest.raises(ModelError, match="GEMINI_API_KEY"):
        GeminiAdapter(api_key="")


# -------------------------------------------------------------------- factory
def test_factory_construye_mock(tmp_path: Path):
    config = Config(data_dir=str(tmp_path))
    config.model.provider = "mock"
    assert isinstance(build_adapter(config), MockAdapter)


def test_factory_construye_ollama_sin_clave(tmp_path: Path):
    config = Config(data_dir=str(tmp_path))
    config.model.provider = "ollama"
    config.model.name = "llama3.1"
    adapter = build_adapter(config)
    assert isinstance(adapter, OpenAICompatibleAdapter)
    assert adapter.base_url.startswith("http://localhost:11434")


def test_factory_openai_sin_clave_falla(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = Config(data_dir=str(tmp_path))
    config.model.provider = "openai"
    with pytest.raises(ModelError, match="clave"):
        build_adapter(config)
