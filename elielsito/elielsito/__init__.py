"""Elielsito AI — asistente personal modular."""

from .config import Config
from .core import Agent
from .identity import IDENTITY

__all__ = ["Config", "Agent", "IDENTITY"]
__version__ = "0.2.0"
