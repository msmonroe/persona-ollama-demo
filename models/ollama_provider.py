"""
Ollama model provider implementation.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Generator
import os
import time
import requests
from . import ModelProvider
from instrumentation import instrumentation


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
            models = [model["name"] for model in data.get("models", [])]
            
            # Sort models with preferred ones first (smaller models that are likely to work)
            preferred_order = ['llama3.2:latest', 'llama3.2:3b', 'llama3.1:8b', 'mistral:latest']
            sorted_models = []
            
            # Add preferred models first if they exist
            for preferred in preferred_order:
                if preferred in models:
                    sorted_models.append(preferred)
                    models.remove(preferred)
            
            # Add remaining models
            sorted_models.extend(models)
            return sorted_models
            
        except:
            return ["llama3.2:latest", "llama3.2:3b", "llama3.1:8b", "mistral:latest"]  # Fallback defaults

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
        start_time = time.time()
        try:
            url = f"{self._base_url()}/api/chat"
            payload = {
                "model": model,
                "stream": False,
                "messages": [{"role": "system", "content": system_prompt}] + messages,
            }

            response = requests.post(url, json=payload, timeout=timeout_s)
            response.raise_for_status()
            data = response.json()
            result = data["message"]["content"]
            
            duration = time.time() - start_time
            instrumentation.log_operation("ollama_chat", True, duration, 
                                        model=model, message_count=len(messages), 
                                        response_length=len(result))
            return result
        except Exception as e:
            duration = time.time() - start_time
            instrumentation.log_operation("ollama_chat", False, duration, e,
                                        model=model, message_count=len(messages))
            raise

    def chat_stream(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        timeout_s: int = 120,
        **kwargs
    ) -> Generator[str, None, None]:
        """Streaming chat completion."""
        start_time = time.time()
        total_content = ""
        try:
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
                            content = data["message"]["content"]
                            total_content += content
                            yield content
                        if data.get("done", False):
                            break
            
            duration = time.time() - start_time
            instrumentation.log_operation("ollama_chat_stream", True, duration,
                                        model=model, message_count=len(messages),
                                        response_length=len(total_content))
        except Exception as e:
            duration = time.time() - start_time
            instrumentation.log_operation("ollama_chat_stream", False, duration, e,
                                        model=model, message_count=len(messages),
                                        partial_response_length=len(total_content))
            raise

    def health_check(self) -> bool:
        """Check if Ollama is running."""
        start_time = time.time()
        try:
            response = requests.get(f"{self._base_url()}/api/tags", timeout=5)
            response.raise_for_status()
            duration = time.time() - start_time
            instrumentation.log_operation("ollama_health_check", True, duration)
            return True
        except Exception as e:
            duration = time.time() - start_time
            instrumentation.log_operation("ollama_health_check", False, duration, e)
            return False