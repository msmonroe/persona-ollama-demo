"""
Model provider registry setup.
"""
from . import registry
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider
from .xai_provider import xAIProvider
from .deepseek_provider import DeepSeekProvider


def setup_providers():
    """Register all available model provider classes."""
    registry.register(OllamaProvider)
    registry.register(OpenAIProvider)
    registry.register(AnthropicProvider)
    registry.register(GoogleProvider)
    registry.register(xAIProvider)
    registry.register(DeepSeekProvider)


# Auto-setup providers when module is imported
setup_providers()