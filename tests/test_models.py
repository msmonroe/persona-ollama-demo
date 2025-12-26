"""
Tests for model providers.
"""
import pytest
from unittest.mock import patch, Mock
from models import registry
from models.ollama_provider import OllamaProvider
from models.providers import setup_providers


class TestModelRegistry:
    """Tests for the model provider registry."""

    def setup_method(self):
        """Set up providers before each test."""
        setup_providers()

    def test_registry_has_providers(self):
        """Test that registry has providers registered."""
        assert len(registry.get_available_providers()) > 0
        assert "Ollama" in registry.get_available_providers()

    def test_get_provider_returns_correct_provider(self):
        """Test getting a provider by name."""
        provider = registry.get_provider("Ollama")
        assert provider is not None
        assert provider.name == "Ollama"

    def test_get_provider_for_model(self):
        """Test finding provider for a specific model."""
        provider = registry.get_provider_for_model("llama3.2:latest")
        assert provider is not None
        assert provider.name == "Ollama"


class TestOllamaProvider:
    """Tests for Ollama provider."""

    def test_ollama_provider_creation(self):
        """Test creating an Ollama provider."""
        provider = OllamaProvider()
        assert provider.name == "Ollama"
        assert len(provider.available_models) >= 0  # May be empty if Ollama not running

    @patch('models.ollama_provider.requests.get')
    def test_health_check_success(self, mock_get):
        """Test health check when Ollama is available."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        provider = OllamaProvider()
        assert provider.health_check() is True

    @patch('models.ollama_provider.requests.get')
    def test_health_check_failure(self, mock_get):
        """Test health check when Ollama is not available."""
        mock_get.side_effect = Exception("Connection failed")

        provider = OllamaProvider()
        assert provider.health_check() is False