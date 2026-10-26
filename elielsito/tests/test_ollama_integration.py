"""Prueba de integración real con un servidor compatible con Ollama.

Levanta un servidor HTTP local que imita la API `/v1/chat/completions` de Ollama
y hace que el agente hable con él por HTTP de verdad (sin modelos ni claves).

Esto verifica el camino completo: configuración -> fábrica de adaptadores ->
adaptador OpenAI-compatible -> petición HTTP -> parseo -> bucle del agente.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from elielsito.config import Config
from elielsito.core import Agent


class _FakeOllama(BaseHTTPRequestHandler):
    # Cola de respuestas que el servidor devolverá en orden.
    respuestas: list[dict] = []
    peticiones: list[dict] = []

    def do_POST(self) -> None:  # noqa: N802 (nombre exigido por http.server)
        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo = json.loads(self.rfile.read(longitud) or b"{}")
        type(self).peticiones.append(cuerpo)

        respuesta = (
            type(self).respuestas.pop(0)
            if type(self).respuestas
            else {
                "model": cuerpo.get("model", "fake"),
                "choices": [
                    {"finish_reason": "stop", "message": {"role": "assistant", "content": "sin guion"}}
                ],
            }
        )
        datos = json.dumps(respuesta).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, *args) -> None:  # silencia el log del servidor
        pass


@pytest.fixture()
def ollama_falso():
    _FakeOllama.respuestas = []
    _FakeOllama.peticiones = []
    servidor = HTTPServer(("127.0.0.1", 0), _FakeOllama)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        yield f"http://127.0.0.1:{servidor.server_port}/v1"
    finally:
        servidor.shutdown()


def _config(tmp_path: Path, base_url: str) -> Config:
    config = Config(data_dir=str(tmp_path / "datos"))
    config.model.provider = "ollama"
    config.model.name = "qwen2.5:7b"
    config.model.base_url = base_url
    config.safety.allowed_roots = [str(tmp_path)]
    return config


def test_conversacion_contra_servidor_compatible(tmp_path: Path, ollama_falso: str):
    _FakeOllama.respuestas = [
        {
            "model": "qwen2.5:7b",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "Aquí estoy, jefe. ¿Qué hacemos?"},
                }
            ],
            "usage": {"total_tokens": 21},
        }
    ]

    agent = Agent(_config(tmp_path, ollama_falso), approve=lambda *a: True)
    resultado = agent.chat("Hola Elielsito")
    agent.close()

    assert resultado.reply == "Aquí estoy, jefe. ¿Qué hacemos?"
    assert resultado.stopped_reason == "stop"
    assert resultado.model == "qwen2.5:7b"


def test_el_agente_envia_el_prompt_de_sistema_y_las_herramientas(tmp_path: Path, ollama_falso: str):
    _FakeOllama.respuestas = [
        {"choices": [{"finish_reason": "stop", "message": {"content": "ok"}}]}
    ]
    agent = Agent(_config(tmp_path, ollama_falso), approve=lambda *a: True)
    agent.chat("Hola")
    agent.close()

    peticion = _FakeOllama.peticiones[-1]
    assert peticion["model"] == "qwen2.5:7b"
    assert peticion["messages"][0]["role"] == "system"
    assert "Elielsito" in peticion["messages"][0]["content"]
    assert any(t["function"]["name"] == "write_file" for t in peticion["tools"])


def test_ciclo_de_herramienta_completo_por_http(tmp_path: Path, ollama_falso: str):
    """El servidor pide una herramienta; el agente la ejecuta y le devuelve el resultado."""
    _FakeOllama.respuestas = [
        {
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": "",
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {
                                    "name": "write_file",
                                    "arguments": json.dumps(
                                        {"path": str(tmp_path / "salida.txt"), "content": "desde ollama"}
                                    ),
                                },
                            }
                        ],
                    },
                }
            ]
        },
        {
            "choices": [
                {"finish_reason": "stop", "message": {"content": "Archivo creado, jefe."}}
            ]
        },
    ]

    agent = Agent(_config(tmp_path, ollama_falso), approve=lambda *a: True)
    resultado = agent.chat("escribe un archivo")
    agent.close()

    assert resultado.reply == "Archivo creado, jefe."
    assert resultado.tool_calls == 1
    assert (tmp_path / "salida.txt").read_text(encoding="utf-8") == "desde ollama"

    # La segunda petición debe incluir el resultado de la herramienta.
    segunda = _FakeOllama.peticiones[-1]
    assert any(m.get("role") == "tool" for m in segunda["messages"])
