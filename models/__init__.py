"""
Model provider abstraction for multiple AI services.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Generator
import os


class ModelProvider(ABC):
    """Abstract base class for AI model providers."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._get_api_key()

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'OpenAI', 'Anthropic')."""
        pass

    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """List of available model names for this provider."""
        pass

    @abstractmethod
    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment variables."""
        pass

    @abstractmethod
    def chat(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Non-streaming chat completion."""
        pass

    @abstractmethod
    def chat_stream(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[str, None, None]:
        """Streaming chat completion."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the provider is accessible."""
        pass


class ModelProviderRegistry:
    """Registry for managing model providers."""

    def __init__(self):
        self._provider_classes: Dict[str, type] = {}
        self._provider_instances: Dict[str, ModelProvider] = {}

    def register(self, provider_class: type) -> None:
        """Register a model provider class."""
        # Get the name from the class without instantiating
        name = getattr(provider_class, 'provider_name', provider_class.__name__.replace('Provider', ''))
        self._provider_classes[name] = provider_class

    def get_provider(self, name: str) -> Optional[ModelProvider]:
        """Get a provider instance by name (lazy instantiation)."""
        if name not in self._provider_instances:
            if name in self._provider_classes:
                self._provider_instances[name] = self._provider_classes[name]()
        return self._provider_instances.get(name)

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return list(self._provider_classes.keys())

    def get_provider_for_model(self, model_name: str) -> Optional[ModelProvider]:
        """Find provider that supports a specific model."""
        for provider_name in self._provider_classes:
            provider = self.get_provider(provider_name)
            if provider and model_name in provider.available_models:
                return provider
        return None


# Global registry instance
registry = ModelProviderRegistry()