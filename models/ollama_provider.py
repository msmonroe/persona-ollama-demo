"""
Ollama model provider implementation.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Generator
import os
import requests
from . import ModelProvider


class OllamaProvider(ModelProvider):
    """Ollama model provider."""
    
    provider_name = "Ollama"

    @property
    def name(self) -> str:
        return "Ollama"

    @property
    def available_models(self) -> List[str]:
        """Get available models from Ollama."""
        try:
            response = requests.get(f"{self._base_url()}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        except:
            return ["llama3.2", "llama3.1", "mistral", "codellama"]  # Fallback defaults

    def _get_api_key(self) -> Optional[str]:
        return None  # Ollama doesn't use API keys

    def _base_url(self) -> str:
        return os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")

    def chat(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        timeout_s: int = 120,
        **kwargs
    ) -> str:
        """Non-streaming chat completion."""
        url = f"{self._base_url()}/api/chat"
        payload = {
            "model": model,
            "stream": False,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
        }

        response = requests.post(url, json=payload, timeout=timeout_s)
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]

    def chat_stream(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        timeout_s: int = 120,
        **kwargs
    ) -> Generator[str, None, None]:
        """Streaming chat completion."""
        url = f"{self._base_url()}/api/chat"
        payload = {
            "model": model,
            "stream": True,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
        }

        with requests.post(url, json=payload, timeout=timeout_s, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]
                    if data.get("done", False):
                        break

    def health_check(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self._base_url()}/api/tags", timeout=5)
            response.raise_for_status()
            return True
        except:
            return False