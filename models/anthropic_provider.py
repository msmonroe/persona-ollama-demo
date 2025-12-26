"""
Anthropic (Claude) model provider implementation.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Generator
import os
from anthropic import Anthropic
from . import ModelProvider


class AnthropicProvider(ModelProvider):
    """Anthropic Claude model provider."""
    
    provider_name = "Anthropic"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._client = None

    @property
    def client(self):
        """Lazy initialization of Anthropic client."""
        if self._client is None and self.api_key:
            self._client = Anthropic(api_key=self.api_key)
        return self._client

    @property
    def name(self) -> str:
        return "Anthropic"

    @property
    def available_models(self) -> List[str]:
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
        ]

    def _get_api_key(self) -> Optional[str]:
        return os.getenv("ANTHROPIC_API_KEY")

    def chat(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        **kwargs
    ) -> str:
        """Non-streaming chat completion."""
        try:
            # Convert messages format for Anthropic
            anthropic_messages = []
            for msg in messages:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=anthropic_messages,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Anthropic API error: {e}")

    def chat_stream(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        **kwargs
    ) -> Generator[str, None, None]:
        """Streaming chat completion."""
        try:
            # Convert messages format for Anthropic
            anthropic_messages = []
            for msg in messages:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=anthropic_messages,
                stream=True,
                **kwargs
            )

            for chunk in response:
                if chunk.type == "content_block_delta" and chunk.delta.text:
                    yield chunk.delta.text
        except Exception as e:
            raise Exception(f"Anthropic API error: {e}")

    def health_check(self) -> bool:
        """Check if Anthropic API is accessible."""
        try:
            # Simple test request
            self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hello"}]
            )
            return True
        except:
            return False