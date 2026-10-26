"""Fábrica de adaptadores: convierte la configuración en un adaptador concreto."""

from __future__ import annotations

import os

from ..config import Config
from .anthropic import AnthropicAdapter
from .base import ModelAdapter, ModelError
from .gemini import GeminiAdapter
from .mock import MockAdapter
from .openai_compatible import OpenAICompatibleAdapter


def build_adapter(config: Config) -> ModelAdapter:
    provider = config.model.provider
    model = config.model.name

    if provider == "mock":
        return MockAdapter(model=model)

    if provider == "ollama":
        # Servidor local compatible con OpenAI. No requiere clave.
        return OpenAICompatibleAdapter(
            model=model,
            api_key=os.environ.get("OLLAMA_API_KEY") or "ollama",
            base_url=config.model.base_url or "http://localhost:11434/v1",
            temperature=config.model.temperature,
            max_tokens=config.model.max_tokens,
            timeout=config.model.timeout,
            requires_key=False,
            label="ollama (local)",
        )

    if provider == "openai":
        return OpenAICompatibleAdapter(
            model=model,
            api_key=os.environ.get("OPENAI_API_KEY"),
            base_url=config.model.base_url or "https://api.openai.com/v1",
            temperature=config.model.temperature,
            max_tokens=config.model.max_tokens,
            timeout=config.model.timeout,
            label="openai",
        )

    if provider == "anthropic":
        return AnthropicAdapter(
            model=model,
            api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            temperature=config.model.temperature,
            max_tokens=config.model.max_tokens,
            timeout=config.model.timeout,
        )

    if provider == "gemini":
        return GeminiAdapter(
            model=model,
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            temperature=config.model.temperature,
            max_tokens=config.model.max_tokens,
            timeout=config.model.timeout,
        )

    raise ModelError(f"Proveedor no soportado: {provider!r}")
