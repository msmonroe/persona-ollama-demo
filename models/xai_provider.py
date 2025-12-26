"""
xAI (Grok) model provider implementation.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Generator
import os
from openai import OpenAI
from . import ModelProvider


class xAIProvider(ModelProvider):
    """xAI Grok model provider."""
    
    provider_name = "xAI"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._client = None

    @property
    def client(self):
        """Lazy initialization of xAI client."""
        if self._client is None and self.api_key:
            self._client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.x.ai/v1"
            )
        return self._client

    @property
    def name(self) -> str:
        return "xAI"

    @property
    def available_models(self) -> List[str]:
        return [
            "grok-beta",
            "grok-vision-beta",
        ]

    def _get_api_key(self) -> Optional[str]:
        return os.getenv("XAI_API_KEY")

    def chat(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Non-streaming chat completion."""
        if not self.client:
            raise Exception("xAI API key not configured")
            
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"xAI API error: {e}")

    def chat_stream(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[str, None, None]:
        """Streaming chat completion."""
        if not self.client:
            raise Exception("xAI API key not configured")
            
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                stream=True,
                **kwargs
            )

            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise Exception(f"xAI API error: {e}")

    def health_check(self) -> bool:
        """Check if xAI API is accessible."""
        if not self.client:
            return False
            
        try:
            # Simple test request
            self.client.models.list()
            return True
        except:
            return False