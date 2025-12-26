"""Ollama client module for chat interactions."""

from .client import chat, health_check, OllamaConnectionError

__all__ = [
    "chat",
    "health_check",
    "OllamaConnectionError",
]
