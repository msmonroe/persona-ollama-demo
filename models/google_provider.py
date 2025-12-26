"""
Google (Gemini) model provider implementation.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Generator
import os
import google.genai as genai
from . import ModelProvider


class GoogleProvider(ModelProvider):
    """Google Gemini model provider."""
    
    provider_name = "Google"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._client = None

    def _ensure_initialized(self):
        """Lazy initialization of Google client."""
        if self._client is None and self.api_key:
            self._client = genai.Client(api_key=self.api_key)

    @property
    def client(self):
        """Lazy initialization of Google client."""
        self._ensure_initialized()
        return self._client

    @property
    def name(self) -> str:
        return "Google"

    @property
    def available_models(self) -> List[str]:
        return [
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
        ]

    def _get_api_key(self) -> Optional[str]:
        return os.getenv("GOOGLE_API_KEY")

    def chat(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Non-streaming chat completion."""
        if not self.api_key:
            raise Exception("Google API key not configured")
            
        try:
            # Convert messages to Gemini format
            contents = []
            
            # Add system prompt as first user message
            contents.append({
                "role": "user",
                "parts": [{"text": f"System: {system_prompt}"}]
            })
            
            # Add conversation history
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

            response = self.client.models.generate_content(
                model=model,
                contents=contents
            )

            return response.text
        except Exception as e:
            raise Exception(f"Google API error: {e}")

    def chat_stream(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[str, None, None]:
        """Streaming chat completion."""
        if not self.api_key:
            raise Exception("Google API key not configured")
            
        try:
            # Convert messages to Gemini format
            contents = []
            
            # Add system prompt as first user message
            contents.append({
                "role": "user",
                "parts": [{"text": f"System: {system_prompt}"}]
            })
            
            # Add conversation history
            for msg in messages:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

            response = self.client.models.generate_content_stream(
                model=model,
                contents=contents
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise Exception(f"Google API error: {e}")

    def health_check(self) -> bool:
        """Check if Google API is accessible."""
        if not self.api_key:
            return False
            
        try:
            # Simple test request
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=[{"role": "user", "parts": [{"text": "Hello"}]}]
            )
            return bool(response.text)
        except:
            return False