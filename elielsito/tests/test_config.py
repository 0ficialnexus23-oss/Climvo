"""Pruebas de configuración: valores por defecto, persistencia y validación."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from elielsito.config import Config, MemoryConfig, ModelConfig, SafetyConfig


def test_valores_por_defecto():
    config = Config()
    assert config.app_name == "Elielsito"
    assert config.model.provider == "mock"
    assert config.safety.allow_shell is False
    assert config.safety.max_steps == 12
    assert "execute" in config.safety.require_approval
    config.validate()


def test_guardar_y_cargar(tmp_path: Path):
    config = Config(data_dir=str(tmp_path / "datos"))
    config.model.provider = "ollama"
    config.model.name = "llama3"
    config.safety.allowed_roots = [str(tmp_path / "proyectos")]
    ruta = config.save()

    assert ruta.exists()
    recargada = Config.load(ruta)
    assert recargada.model.provider == "ollama"
    assert recargada.model.name == "llama3"
    assert recargada.safety.allowed_roots == [str(tmp_path / "proyectos")]


def test_variables_de_entorno_tienen_prioridad(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ELELSITO_MODEL_PROVIDER", "gemini")
    monkeypatch.setenv("ELELSITO_MODEL_NAME", "gemini-2.0-flash")
    monkeypatch.setenv("ELELSITO_ALLOW_SHELL", "1")
    monkeypatch.setenv("ELELSITO_DATA_DIR", str(tmp_path / "otro"))

    config = Config.load(tmp_path / "inexistente.json")
    assert config.model.provider == "gemini"
    assert config.model.name == "gemini-2.0-flash"
    assert config.safety.allow_shell is True
    assert config.data_dir == str(tmp_path / "otro")


def test_archivo_corrupto_falla_claro(tmp_path: Path):
    ruta = tmp_path / "config.json"
    ruta.write_text("{ esto no es json", encoding="utf-8")
    with pytest.raises(ValueError, match="dañado"):
        Config.load(ruta)


def test_validacion_de_proveedor():
    config = Config()
    config.model.provider = "inventado"
    with pytest.raises(ValueError, match="Proveedor"):
        config.validate()


def test_validacion_de_limites():
    with pytest.raises(ValueError):
        ModelConfig(temperature=5.0).validate()
    with pytest.raises(ValueError):
        SafetyConfig(max_steps=0).validate()
    with pytest.raises(ValueError):
        MemoryConfig(max_items=0).validate()


def test_rutas_derivadas(tmp_path: Path):
    config = Config(data_dir=str(tmp_path))
    assert config.memory_db == tmp_path / "memory.db"
    assert config.audit_file == tmp_path / "audit.log"
    assert tmp_path.resolve() in config.allowed_roots()


def test_carga_desde_data_dir_de_entorno(tmp_path: Path, monkeypatch):
    """ELELSITO_DATA_DIR debe determinar dónde se busca config.json."""
    monkeypatch.setenv("ELELSITO_DATA_DIR", str(tmp_path))
    config = Config(data_dir=str(tmp_path))
    config.model.name = "modelo-guardado"
    config.save()

    recargada = Config.load()
    assert recargada.model.name == "modelo-guardado"


def test_guardado_es_atomico(tmp_path: Path):
    """Tras guardar no debe quedar ningún archivo temporal."""
    config = Config(data_dir=str(tmp_path))
    ruta = config.save()
    assert json.loads(ruta.read_text(encoding="utf-8"))["app_name"] == "Elielsito"
    assert not list(tmp_path.glob("*.tmp"))
