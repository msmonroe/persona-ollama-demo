"""
OpenAI model provider implementation.
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Generator
import os
import time
from openai import OpenAI
from . import ModelProvider
from instrumentation import instrumentation


class OpenAIProvider(ModelProvider):
    """OpenAI model provider."""
    
    provider_name = "OpenAI"

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self._client = None

    @property
    def client(self):
        """Lazy initialization of OpenAI client."""
        if self._client is None and self.api_key:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    @property
    def name(self) -> str:
        return "OpenAI"

    @property
    def available_models(self) -> List[str]:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ]

    def _get_api_key(self) -> Optional[str]:
        return os.getenv("OPENAI_API_KEY")

    def chat(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Non-streaming chat completion."""
        start_time = time.time()
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                **kwargs
            )
            result = response.choices[0].message.content
            duration = time.time() - start_time
            instrumentation.log_operation("openai_chat", True, duration,
                                        model=model, message_count=len(messages),
                                        response_length=len(result))
            return result
        except Exception as e:
            duration = time.time() - start_time
            instrumentation.log_operation("openai_chat", False, duration, e,
                                        model=model, message_count=len(messages))
            raise Exception(f"OpenAI API error: {e}")

    def chat_stream(
        self,
        model: str,
        system_prompt: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Generator[str, None, None]:
        """Streaming chat completion."""
        start_time = time.time()
        total_content = ""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                stream=True,
                **kwargs
            )

            for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    total_content += content
                    yield content
            
            duration = time.time() - start_time
            instrumentation.log_operation("openai_chat_stream", True, duration,
                                        model=model, message_count=len(messages),
                                        response_length=len(total_content))
        except Exception as e:
            duration = time.time() - start_time
            instrumentation.log_operation("openai_chat_stream", False, duration, e,
                                        model=model, message_count=len(messages),
                                        partial_response_length=len(total_content))
            raise Exception(f"OpenAI API error: {e}")

    def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        start_time = time.time()
        try:
            # Simple test request
            self.client.models.list(limit=1)
            duration = time.time() - start_time
            instrumentation.log_operation("openai_health_check", True, duration)
            return True
        except Exception as e:
            duration = time.time() - start_time
            instrumentation.log_operation("openai_health_check", False, duration, e)
            return False