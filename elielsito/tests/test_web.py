"""Pruebas de la interfaz web (FastAPI) con el motor simulado.

No requieren Ollama ni red: usan `TestClient` y el proveedor `mock`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from elielsito.config import Config
from elielsito.web.app import create_app


@pytest.fixture()
def client(tmp_path: Path):
    config = Config(data_dir=str(tmp_path / "datos"))
    config.model.provider = "mock"
    config.model.name = "mock-1"
    config.safety.allowed_roots = [str(tmp_path)]
    app = create_app(config)
    with TestClient(app) as test_client:
        yield test_client


# ------------------------------------------------------------------ páginas
def test_index_sirve_la_interfaz(client: TestClient):
    respuesta = client.get("/")
    assert respuesta.status_code == 200
    assert "Elielsito" in respuesta.text
    assert "/static/app.js" in respuesta.text
    assert "/static/app.css" in respuesta.text


def test_estaticos_disponibles(client: TestClient):
    css = client.get("/static/app.css")
    js = client.get("/static/app.js")
    assert css.status_code == 200 and "--accent" in css.text
    assert js.status_code == 200 and "sendMessage" in js.text


def test_health(client: TestClient):
    assert client.get("/health").json() == {"status": "ok"}


# ------------------------------------------------------------------ estado
def test_status_expone_configuracion_real(client: TestClient):
    datos = client.get("/api/status").json()
    assert datos["provider"] == "mock"
    assert datos["model"] == "mock-1"
    assert datos["identity"]["name"] == "Elielsito"
    assert datos["shell_allowed"] is False
    assert datos["limits"]["max_steps"] == 12


def test_tools_lista_las_cinco_herramientas(client: TestClient):
    nombres = {t["name"] for t in client.get("/api/tools").json()}
    assert {
        "read_file",
        "write_file",
        "list_dir",
        "memory_save",
        "memory_search",
    } <= nombres


# -------------------------------------------------------------------- chat
def test_chat_responde(client: TestClient):
    respuesta = client.post("/api/chat", json={"message": "Hola Elielsito"})
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["reply"]
    assert datos["stopped_reason"] == "stop"
    assert datos["model"] == "mock-1"


def test_chat_rechaza_mensaje_vacio(client: TestClient):
    respuesta = client.post("/api/chat", json={"message": ""})
    assert respuesta.status_code == 422


def test_chat_acepta_historial(client: TestClient):
    respuesta = client.post(
        "/api/chat",
        json={
            "message": "¿y ahora?",
            "history": [
                {"role": "user", "content": "antes"},
                {"role": "assistant", "content": "respuesta anterior"},
            ],
        },
    )
    assert respuesta.status_code == 200


# ----------------------------------------------------------------- memoria
def test_memoria_ciclo_completo(client: TestClient):
    creado = client.post(
        "/api/memory",
        json={"content": "El usuario prefiere respuestas directas", "category": "personal"},
    )
    assert creado.status_code == 201
    item = creado.json()["item"]
    assert item["category"] == "personal"

    listado = client.get("/api/memory").json()
    assert any(i["id"] == item["id"] for i in listado)

    borrado = client.delete(f"/api/memory/{item['id']}")
    assert borrado.status_code == 200
    assert borrado.json()["deleted"] is True


def test_memoria_busqueda(client: TestClient):
    client.post("/api/memory", json={"content": "La base de datos es SQLite"})
    resultados = client.get("/api/memory", params={"q": "SQLite"}).json()
    assert resultados and "SQLite" in resultados[0]["content"]


def test_memoria_categoria_invalida(client: TestClient):
    respuesta = client.post("/api/memory", json={"content": "algo", "category": "inventada"})
    assert respuesta.status_code == 400


def test_memoria_rechaza_secretos(client: TestClient):
    respuesta = client.post(
        "/api/memory",
        json={"content": "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456"},
    )
    assert respuesta.status_code == 400
    assert "secreto" in respuesta.json()["detail"].lower()


# --------------------------------------------------------------- auditoría
def test_auditoria_registra_el_chat(client: TestClient):
    client.post("/api/chat", json={"message": "hola"})
    eventos = client.get("/api/audit").json()
    assert any(e["event"] == "chat_start" for e in eventos)
    assert any(e["event"] == "chat_end" for e in eventos)
