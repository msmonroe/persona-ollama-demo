"""
Google (Gemini) model provider implementation.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Generator
import os
import google.generativeai as genai
from . import ModelProvider


class GoogleProvider(ModelProvider):
    """Google Gemini model provider."""
    
    provider_name = "Google"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of Google client."""
        if not self._initialized and self.api_key:
            genai.configure(api_key=self.api_key)
            self._initialized = True

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
        self._ensure_initialized()
        if not self.api_key:
            raise Exception("Google API key not configured")
            
        try:
            model_instance = genai.GenerativeModel(model)

            # Convert messages to Gemini format
            history = []
            for msg in messages[:-1]:  # All but last message
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})

            chat = model_instance.start_chat(history=history)

            # Send the last message
            last_message = messages[-1]["content"] if messages else ""
            response = chat.send_message(f"System: {system_prompt}\n\n{last_message}")

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
        self._ensure_initialized()
        if not self.api_key:
            raise Exception("Google API key not configured")
            
        try:
            model_instance = genai.GenerativeModel(model)

            # Convert messages to Gemini format
            history = []
            for msg in messages[:-1]:  # All but last message
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})

            chat = model_instance.start_chat(history=history)

            # Send the last message with streaming
            last_message = messages[-1]["content"] if messages else ""
            response = chat.send_message(
                f"System: {system_prompt}\n\n{last_message}",
                stream=True
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise Exception(f"Google API error: {e}")

    def health_check(self) -> bool:
        """Check if Google API is accessible."""
        self._ensure_initialized()
        if not self.api_key:
            return False
            
        try:
            # Simple test request
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content("Hello")
            return bool(response.text)
        except:
            return False