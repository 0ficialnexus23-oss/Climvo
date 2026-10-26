"""Adaptadores de modelo de IA (intercambiables)."""

from .base import Message, ModelAdapter, ModelError, ModelResponse, ToolCall
from .factory import build_adapter
from .mock import MockAdapter

__all__ = [
    "Message",
    "ModelAdapter",
    "ModelError",
    "ModelResponse",
    "ToolCall",
    "MockAdapter",
    "build_adapter",
]
