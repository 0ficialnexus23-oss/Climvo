"""Pruebas de la memoria persistente."""

from __future__ import annotations

from pathlib import Path

import pytest

from elielsito.memory.store import MemoryStore, looks_secret


@pytest.fixture()
def store(tmp_path: Path):
    store = MemoryStore(tmp_path / "memoria.db")
    yield store
    store.close()


def test_guardar_y_recuperar(store: MemoryStore):
    item, creado = store.add("Al usuario le gusta el café sin azúcar", category="personal")
    assert creado is True
    assert item.id > 0
    assert item.kind == "fact"
    assert store.get(item.id).content.startswith("Al usuario")


def test_deduplicacion(store: MemoryStore):
    primero, creado1 = store.add("Proyecto Elielsito usa Python", category="project")
    segundo, creado2 = store.add("Proyecto   Elielsito usa Python", category="project")
    assert creado1 is True
    assert creado2 is False
    assert primero.id == segundo.id
    assert store.stats()["_total"] == 1


def test_busqueda_encuentra_por_relevancia(store: MemoryStore):
    store.add("La base de datos es SQLite", category="project")
    store.add("El usuario prefiere respuestas cortas", category="personal")
    resultados = store.search("SQLite")
    assert resultados
    assert "SQLite" in resultados[0].content


def test_filtro_por_categoria(store: MemoryStore):
    store.add("Dato de proyecto", category="project")
    store.add("Dato personal", category="personal")
    solo_personal = store.search("dato", category="personal")
    assert all(i.category == "personal" for i in solo_personal)


def test_rechaza_secretos(store: MemoryStore):
    with pytest.raises(ValueError, match="secreto"):
        store.add("OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz123456")
    with pytest.raises(ValueError, match="secreto"):
        store.add("mi password: hunter2")


def test_categorias_y_tipos_invalidos(store: MemoryStore):
    with pytest.raises(ValueError, match="Categoría"):
        store.add("algo", category="inventada")
    with pytest.raises(ValueError, match="Tipo"):
        store.add("algo", kind="inventado")
    with pytest.raises(ValueError, match="vacío"):
        store.add("   ")


def test_hipotesis_vs_hecho(store: MemoryStore):
    item, _ = store.add("Quizá conviene usar Postgres", category="project", kind="hypothesis")
    assert item.kind == "hypothesis"
    assert "HIPÓTESIS" in item.render()


def test_actualizacion_conserva_id(store: MemoryStore):
    item, _ = store.add("El usuario trabaja de noche", category="personal")
    actualizado, creado = store.add(
        "El usuario trabaja de noche", category="personal", source="conversación 2026-10-15"
    )
    assert creado is False
    assert actualizado.id == item.id
    assert actualizado.source == "conversación 2026-10-15"


def test_borrado_y_exportacion(store: MemoryStore):
    item, _ = store.add("Recuerdo temporal", category="operational")
    assert store.delete(item.id) is True
    assert store.delete(item.id) is False

    store.add("Uno", category="knowledge")
    store.add("Dos", category="knowledge")
    exportado = store.export()
    assert len(exportado) == 2
    assert {"id", "category", "content", "kind"} <= set(exportado[0])


def test_respaldo(tmp_path: Path, store: MemoryStore):
    store.add("Dato para respaldar", category="knowledge")
    destino = store.backup(tmp_path / "copias")
    assert destino.exists() and destino.stat().st_size > 0

    copia = MemoryStore(destino)
    assert copia.search("respaldar")
    copia.close()


def test_contexto_para_prompt(store: MemoryStore):
    store.add("El usuario se llama Eliel", category="personal")
    contexto = store.context_for("¿cómo me llamo?")
    assert "Eliel" in contexto


def test_deteccion_de_secretos():
    assert looks_secret("sk-proj-abcdefghijklmnopqrstuvwx")
    assert looks_secret("ghp_abcdefghijklmnopqrstuvwxyz0123456789")
    assert not looks_secret("Me gusta el café con leche")
