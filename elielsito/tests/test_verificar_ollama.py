"""Pruebas del verificador de Ollama (sin Ollama real)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

from elielsito.config import Config
from scripts.verificar_ollama import verificar


class _FakeOllama(BaseHTTPRequestHandler):
    modelos = ["qwen2.5:7b", "llama3.2:3b"]

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/tags":
            datos = json.dumps({"models": [{"name": m} for m in type(self).modelos]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(datos)))
            self.end_headers()
            self.wfile.write(datos)
        else:
            self.send_error(404)

    def do_POST(self) -> None:  # noqa: N802
        longitud = int(self.headers.get("Content-Length", 0))
        self.rfile.read(longitud)
        datos = json.dumps(
            {"choices": [{"message": {"role": "assistant", "content": "OK"}}]}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def log_message(self, *args) -> None:
        pass


@pytest.fixture()
def servidor():
    httpd = HTTPServer(("127.0.0.1", 0), _FakeOllama)
    hilo = threading.Thread(target=httpd.serve_forever, daemon=True)
    hilo.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}/v1"
    finally:
        httpd.shutdown()


def _config(tmp_path: Path, base_url: str, modelo: str = "qwen2.5:7b") -> Config:
    config = Config(data_dir=str(tmp_path))
    config.model.provider = "ollama"
    config.model.name = modelo
    config.model.base_url = base_url
    return config


def test_todo_en_verde(tmp_path: Path, servidor: str):
    checks = verificar(_config(tmp_path, servidor))
    assert all(c.ok for c in checks), [c for c in checks if not c.ok]


def test_detecta_modelo_no_descargado(tmp_path: Path, servidor: str):
    checks = verificar(_config(tmp_path, servidor, modelo="modelo-inexistente:70b"))
    modelo = next(c for c in checks if "descargado" in c.nombre)
    assert modelo.ok is False
    assert "ollama pull" in modelo.pista


def test_detecta_proveedor_incorrecto(tmp_path: Path, servidor: str):
    config = _config(tmp_path, servidor)
    config.model.provider = "openai"
    checks = verificar(config)
    primero = checks[0]
    assert primero.ok is False
    assert "configurar_ollama" in primero.pista


def test_detecta_servidor_caido(tmp_path: Path):
    config = _config(tmp_path, "http://127.0.0.1:9/v1", modelo="qwen2.5:7b")
    checks = verificar(config)
    servidor = next(c for c in checks if "Servidor" in c.nombre)
    assert servidor.ok is False
    assert "ollama serve" in servidor.pista
