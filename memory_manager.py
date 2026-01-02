"""
Memory and Context Management for AI conversations.
Handles token limits, context window management, and intelligent message summarization.
"""
from __future__ import annotations
import re
import json
from typing import List, Dict, Any, Optional, Tuple, Protocol
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import tiktoken

from instrumentation import instrumentation


class ContextStrategy(Enum):
    """Strategies for managing conversation context."""
    TRUNCATE_OLDEST = "truncate_oldest"  # Remove oldest messages
    SUMMARIZE_OLDEST = "summarize_oldest"  # Summarize old messages
    KEEP_RECENT = "keep_recent"  # Keep only recent messages
    SLIDING_WINDOW = "sliding_window"  # Use sliding window approach


@dataclass
class TokenUsage:
    """Token usage statistics for a conversation."""
    total_tokens: int
    system_tokens: int
    conversation_tokens: int
    remaining_tokens: int
    max_tokens: int
    utilization_percent: float

    @property
    def is_near_limit(self) -> bool:
        """Check if we're approaching the token limit."""
        return self.utilization_percent > 80.0

    @property
    def is_over_limit(self) -> bool:
        """Check if we're over the token limit."""
        return self.total_tokens > self.max_tokens


@dataclass
class MemoryConfig:
    """Configuration for memory management."""
    max_context_tokens: int = 4000  # Conservative default
    strategy: ContextStrategy = ContextStrategy.SLIDING_WINDOW
    preserve_system_prompt: bool = True
    summarize_threshold: int = 3000  # Start summarizing at this token count
    min_messages_to_keep: int = 4  # Minimum messages to preserve
    enable_auto_summarization: bool = True
    summarization_model: str = "gpt-3.5-turbo"  # Model to use for summarization
    summary_length: int = 200  # Length of conversation summaries in tokens


class MessageSummarizer:
    """Handles intelligent summarization of conversation messages."""

    def __init__(self, config: MemoryConfig):
        self.config = config

    def summarize_messages(self, messages: List[Dict[str, str]], target_tokens: int = 500) -> str:
        """
        Summarize a list of messages into a concise summary.
        This is a simple rule-based summarizer. In production, you'd use an LLM.
        """
        if not messages:
            return ""

        # Extract key information
        user_questions = []
        assistant_responses = []
        topics = set()

        for msg in messages:
            content = msg.get("content", "").lower()

            if msg["role"] == "user":
                # Extract potential questions or topics
                if any(word in content for word in ["what", "how", "why", "when", "where", "can you", "tell me"]):
                    user_questions.append(msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"])
                else:
                    user_questions.append("User input")

                # Extract topics (simple keyword extraction)
                words = re.findall(r'\b\w+\b', content)
                topics.update(word for word in words if len(word) > 4)

            elif msg["role"] == "assistant":
                assistant_responses.append(msg["content"][:150] + "..." if len(msg["content"]) > 150 else msg["content"])

        # Create summary
        summary_parts = []

        if user_questions:
            summary_parts.append(f"Previous discussion covered {len(user_questions)} user questions including: {', '.join(user_questions[:3])}")

        if topics:
            top_topics = list(topics)[:5]
            summary_parts.append(f"Topics discussed: {', '.join(top_topics)}")

        if assistant_responses:
            summary_parts.append(f"Assistant provided {len(assistant_responses)} responses with guidance and information.")

        summary = " ".join(summary_parts)

        # Ensure summary fits within target token limit (rough estimate: 4 chars per token)
        max_chars = target_tokens * 4
        if len(summary) > max_chars:
            summary = summary[:max_chars-3] + "..."

        return f"Summary of earlier conversation: {summary}"

    def should_summarize(self, token_usage: TokenUsage) -> bool:
        """Determine if summarization should be triggered."""
        return (self.config.enable_auto_summarization and
                token_usage.conversation_tokens > self.config.summarize_threshold)


class ContextManager:
    """Manages conversation context and memory."""

    def __init__(self, config: MemoryConfig = None):
        self.config = config or MemoryConfig()
        self.summarizer = MessageSummarizer(self.config)
        self._encoder_cache = {}

    def get_token_encoder(self, model: str) -> tiktoken.Encoding:
        """Get the appropriate token encoder for a model."""
        if model not in self._encoder_cache:
            try:
                # Try to get the appropriate encoder
                if "gpt-4" in model:
                    self._encoder_cache[model] = tiktoken.encoding_for_model("gpt-4")
                elif "gpt-3.5" in model:
                    self._encoder_cache[model] = tiktoken.encoding_for_model("gpt-3.5-turbo")
                else:
                    # Fallback to cl100k_base (used by GPT-3.5 and GPT-4)
                    self._encoder_cache[model] = tiktoken.get_encoding("cl100k_base")
            except Exception:
                # Ultimate fallback
                self._encoder_cache[model] = tiktoken.get_encoding("cl100k_base")

        return self._encoder_cache[model]

    def count_tokens(self, text: str, model: str) -> int:
        """Count tokens in a text string."""
        encoder = self.get_token_encoder(model)
        return len(encoder.encode(text))

    def calculate_token_usage(self, system_prompt: str, messages: List[Dict[str, str]],
                            model: str) -> TokenUsage:
        """Calculate token usage for a conversation."""
        system_tokens = self.count_tokens(system_prompt, model) if system_prompt else 0

        conversation_tokens = 0
        for msg in messages:
            # Add tokens for role and content
            role_tokens = self.count_tokens(msg["role"], model)
            content_tokens = self.count_tokens(msg["content"], model)
            # Rough estimate for message formatting overhead
            conversation_tokens += role_tokens + content_tokens + 4  # 4 tokens for formatting

        total_tokens = system_tokens + conversation_tokens
        max_tokens = self.config.max_context_tokens
        remaining_tokens = max(max_tokens - total_tokens, 0)
        utilization_percent = (total_tokens / max_tokens) * 100 if max_tokens > 0 else 0

        return TokenUsage(
            total_tokens=total_tokens,
            system_tokens=system_tokens,
            conversation_tokens=conversation_tokens,
            remaining_tokens=remaining_tokens,
            max_tokens=max_tokens,
            utilization_percent=utilization_percent
        )

    def optimize_context(self, system_prompt: str, messages: List[Dict[str, str]],
                        model: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Optimize conversation context based on the configured strategy.
        Returns (optimized_system_prompt, optimized_messages)
        """
        start_time = datetime.now()

        try:
            token_usage = self.calculate_token_usage(system_prompt, messages, model)

            # If we're under the limit, no optimization needed
            if not token_usage.is_near_limit:
                instrumentation.log_operation("context_optimization", True, 0.0,
                                            strategy="none", original_tokens=token_usage.total_tokens)
                return system_prompt, messages

            # Apply the configured optimization strategy
            if self.config.strategy == ContextStrategy.TRUNCATE_OLDEST:
                optimized_system, optimized_messages = self._truncate_oldest(system_prompt, messages, model)
            elif self.config.strategy == ContextStrategy.SUMMARIZE_OLDEST:
                optimized_system, optimized_messages = self._summarize_oldest(system_prompt, messages, model)
            elif self.config.strategy == ContextStrategy.KEEP_RECENT:
                optimized_system, optimized_messages = self._keep_recent(system_prompt, messages, model)
            elif self.config.strategy == ContextStrategy.SLIDING_WINDOW:
                optimized_system, optimized_messages = self._sliding_window(system_prompt, messages, model)
            else:
                # Default to sliding window
                optimized_system, optimized_messages = self._sliding_window(system_prompt, messages, model)

            # Calculate new token usage
            new_token_usage = self.calculate_token_usage(optimized_system, optimized_messages, model)

            duration = (datetime.now() - start_time).total_seconds()
            instrumentation.log_operation("context_optimization", True, duration,
                                        strategy=self.config.strategy.value,
                                        original_tokens=token_usage.total_tokens,
                                        optimized_tokens=new_token_usage.total_tokens,
                                        messages_removed=len(messages) - len(optimized_messages))

            return optimized_system, optimized_messages

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            instrumentation.log_operation("context_optimization", False, duration, e,
                                        strategy=self.config.strategy.value)
            # Return original context on error
            return system_prompt, messages

    def _truncate_oldest(self, system_prompt: str, messages: List[Dict[str, str]],
                        model: str) -> Tuple[str, List[Dict[str, str]]]:
        """Truncate oldest messages to fit within token limit."""
        if len(messages) <= self.config.min_messages_to_keep:
            return system_prompt, messages

        # Keep removing oldest messages until we're under the limit
        optimized_messages = messages.copy()

        while len(optimized_messages) > self.config.min_messages_to_keep:
            token_usage = self.calculate_token_usage(system_prompt, optimized_messages, model)
            if not token_usage.is_over_limit:
                break
            # Remove the oldest non-system message pair (question + answer)
            if len(optimized_messages) >= 2:
                optimized_messages = optimized_messages[2:]
            else:
                optimized_messages = optimized_messages[1:]

        return system_prompt, optimized_messages

    def _summarize_oldest(self, system_prompt: str, messages: List[Dict[str, str]],
                         model: str) -> Tuple[str, List[Dict[str, str]]]:
        """Summarize oldest messages and replace them with a summary."""
        if len(messages) <= self.config.min_messages_to_keep:
            return system_prompt, messages

        token_usage = self.calculate_token_usage(system_prompt, messages, model)

        if not self.summarizer.should_summarize(token_usage):
            return system_prompt, messages

        # Find how many messages to summarize
        # Keep at least min_messages_to_keep recent messages
        messages_to_keep = max(self.config.min_messages_to_keep, len(messages) // 2)
        messages_to_summarize = messages[:-messages_to_keep]

        if not messages_to_summarize:
            return system_prompt, messages

        # Create summary
        summary_text = self.summarizer.summarize_messages(messages_to_summarize)

        # Create summary message
        summary_message = {
            "role": "system",
            "content": f"[Context Summary] {summary_text}"
        }

        # Combine summary with recent messages
        optimized_messages = [summary_message] + messages[-messages_to_keep:]

        return system_prompt, optimized_messages

    def _keep_recent(self, system_prompt: str, messages: List[Dict[str, str]],
                    model: str) -> Tuple[str, List[Dict[str, str]]]:
        """Keep only the most recent messages."""
        # Calculate how many recent messages we can keep
        max_messages = self.config.min_messages_to_keep

        # Estimate tokens for recent messages
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages

        token_usage = self.calculate_token_usage(system_prompt, recent_messages, model)

        # If still over limit, reduce further
        while len(recent_messages) > 1 and token_usage.is_over_limit:
            recent_messages = recent_messages[1:]
            token_usage = self.calculate_token_usage(system_prompt, recent_messages, model)

        return system_prompt, recent_messages

    def _sliding_window(self, system_prompt: str, messages: List[Dict[str, str]],
                       model: str) -> Tuple[str, List[Dict[str, str]]]:
        """Use a sliding window approach - keep recent messages, summarize if needed."""
        # First try to keep recent messages
        optimized_system, optimized_messages = self._keep_recent(system_prompt, messages, model)

        # If still over limit after keeping recent, try summarization
        token_usage = self.calculate_token_usage(optimized_system, optimized_messages, model)

        if token_usage.is_over_limit and len(messages) > len(optimized_messages):
            # Try summarization approach
            return self._summarize_oldest(system_prompt, messages, model)

        return optimized_system, optimized_messages

    def get_memory_stats(self, system_prompt: str, messages: List[Dict[str, str]],
                        model: str) -> Dict[str, Any]:
        """Get detailed memory and context statistics."""
        token_usage = self.calculate_token_usage(system_prompt, messages, model)

        return {
            "token_usage": {
                "total": token_usage.total_tokens,
                "system": token_usage.system_tokens,
                "conversation": token_usage.conversation_tokens,
                "remaining": token_usage.remaining_tokens,
                "max": token_usage.max_tokens,
                "utilization_percent": round(token_usage.utilization_percent, 1)
            },
            "message_count": len(messages),
            "strategy": self.config.strategy.value,
            "optimization_needed": token_usage.is_near_limit,
            "over_limit": token_usage.is_over_limit,
            "config": {
                "max_context_tokens": self.config.max_context_tokens,
                "summarize_threshold": self.config.summarize_threshold,
                "min_messages_to_keep": self.config.min_messages_to_keep,
                "auto_summarization": self.config.enable_auto_summarization
            }
        }

    def estimate_tokens(self, messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> int:
        """Estimate total tokens in messages (convenience method)."""
        total_tokens = 0
        for msg in messages:
            # Rough estimation: ~4 tokens per message overhead + content tokens
            total_tokens += self.count_tokens(msg["role"], model)
            total_tokens += self.count_tokens(msg["content"], model)
            total_tokens += 4  # Message formatting overhead
        return total_tokens

    def manage_context(self, messages: List[Dict[str, str]], config: MemoryConfig,
                      strategy: ContextStrategy, provider: str) -> List[Dict[str, str]]:
        """
        Manage conversation context based on strategy.
        This is a simplified interface that doesn't modify system prompts.
        """
        # For now, use a simple token-based approach
        current_tokens = self.estimate_tokens(messages, "gpt-3.5-turbo")  # Default model for estimation

        if current_tokens <= config.max_context_tokens:
            return messages  # No changes needed

        # Apply strategy
        if strategy == ContextStrategy.TRUNCATE_OLDEST:
            # Keep only the most recent messages that fit
            optimized_messages = []
            total_tokens = 0
            max_tokens = config.max_context_tokens

            # Always keep the last message (current user input)
            for msg in reversed(messages):
                msg_tokens = self.count_tokens(msg["role"], "gpt-3.5-turbo") + \
                           self.count_tokens(msg["content"], "gpt-3.5-turbo") + 4

                if total_tokens + msg_tokens <= max_tokens:
                    optimized_messages.insert(0, msg)
                    total_tokens += msg_tokens
                else:
                    break

            return optimized_messages

        elif strategy == ContextStrategy.SUMMARIZE_OLDEST:
            # For now, just truncate but keep more recent messages
            keep_ratio = 0.7  # Keep 70% of messages by recency
            keep_count = max(2, int(len(messages) * keep_ratio))
            return messages[-keep_count:] if len(messages) > keep_count else messages

        elif strategy == ContextStrategy.KEEP_RECENT:
            # Keep only recent messages
            keep_count = max(2, min(len(messages), 10))  # Keep last 10 messages or all if fewer
            return messages[-keep_count:] if len(messages) > keep_count else messages

        elif strategy == ContextStrategy.SLIDING_WINDOW:
            # Use sliding window - keep recent messages within token limit
            return self.manage_context(messages, config, ContextStrategy.TRUNCATE_OLDEST, provider)

        else:
            # Default: truncate oldest
            return self.manage_context(messages, config, ContextStrategy.TRUNCATE_OLDEST, provider)


# Global context manager instance
context_manager = ContextManager()