"""
Model provider registry setup.
"""


def setup_providers(registry):
    """Register all available model provider classes."""
    # Import here to avoid circular imports
    from .ollama_provider import OllamaProvider
    from .openai_provider import OpenAIProvider
    from .anthropic_provider import AnthropicProvider
    from .google_provider import GoogleProvider
    from .xai_provider import xAIProvider
    from .deepseek_provider import DeepSeekProvider
    
    registry.register(OllamaProvider)
    registry.register(OpenAIProvider)
    registry.register(AnthropicProvider)
    registry.register(GoogleProvider)
    registry.register(xAIProvider)
    registry.register(DeepSeekProvider)