from __future__ import annotations
import os
import time
import requests
from typing import List, Dict, Any, Generator, Optional


class OllamaConnectionError(Exception):
    """Raised when unable to connect to Ollama server."""
    pass


def _base_url() -> str:
    return os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")


def health_check(timeout_s: int = 5) -> bool:
    """
    Check if Ollama server is running and accessible.
    Returns True if healthy, raises OllamaConnectionError otherwise.
    """
    try:
        r = requests.get(f"{_base_url()}/api/tags", timeout=timeout_s)
        r.raise_for_status()
        return True
    except requests.exceptions.ConnectionError:
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {_base_url()}. "
            "Make sure Ollama is running (try: ollama serve)"
        )
    except requests.exceptions.Timeout:
        raise OllamaConnectionError(
            f"Ollama at {_base_url()} is not responding (timeout after {timeout_s}s)"
        )
    except requests.exceptions.RequestException as e:
        raise OllamaConnectionError(f"Ollama health check failed: {e}")


def chat(
    model: str,
    system_prompt: str,
    messages: List[Dict[str, str]],
    timeout_s: int = 120,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> str:
    """
    Calls Ollama's /api/chat endpoint (non-streaming).
    messages: list of {"role": "user"|"assistant", "content": "..."}
    
    Args:
        model: The Ollama model to use
        system_prompt: System prompt for persona
        messages: Conversation history
        timeout_s: Request timeout in seconds
        max_retries: Number of retry attempts on failure
        retry_delay: Initial delay between retries (exponential backoff)
    """
    url = f"{_base_url()}/api/chat"
    payload: Dict[str, Any] = {
        "model": model,
        "stream": False,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
    }

    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            r = requests.post(url, json=payload, timeout=timeout_s)
            r.raise_for_status()
            data = r.json()
            return data["message"]["content"]
        except requests.exceptions.ConnectionError as e:
            last_error = OllamaConnectionError(
                f"Cannot connect to Ollama at {_base_url()}. Is it running?"
            )
        except requests.exceptions.Timeout as e:
            last_error = OllamaConnectionError(
                f"Request timed out after {timeout_s}s. Try a smaller model or increase timeout."
            )
        except requests.exceptions.RequestException as e:
            last_error = e

        if attempt < max_retries - 1:
            time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff

    raise last_error or Exception("Unknown error during chat")


def chat_stream(
    model: str,
    system_prompt: str,
    messages: List[Dict[str, str]],
    timeout_s: int = 120,
) -> Generator[str, None, None]:
    """
    Calls Ollama's /api/chat endpoint with streaming.
    Yields content chunks as they arrive.
    
    Args:
        model: The Ollama model to use
        system_prompt: System prompt for persona
        messages: Conversation history
        timeout_s: Request timeout in seconds
    """
    url = f"{_base_url()}/api/chat"
    payload: Dict[str, Any] = {
        "model": model,
        "stream": True,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
    }

    try:
        with requests.post(url, json=payload, timeout=timeout_s, stream=True) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]
                    if data.get("done", False):
                        break
    except requests.exceptions.ConnectionError:
        raise OllamaConnectionError(
            f"Cannot connect to Ollama at {_base_url()}. Is it running?"
        )
    except requests.exceptions.Timeout:
        raise OllamaConnectionError(
            f"Request timed out after {timeout_s}s."
        )
