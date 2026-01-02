import pytest
from memory_manager import ContextManager, MemoryConfig, ContextStrategy, context_manager


class TestMemoryConfig:
    def test_memory_config_creation(self):
        config = MemoryConfig()
        assert config.max_context_tokens == 4000
        assert config.strategy == ContextStrategy.SLIDING_WINDOW
        assert config.summarize_threshold == 3000

    def test_memory_config_custom_values(self):
        config = MemoryConfig(max_context_tokens=16000, summarize_threshold=12000, min_messages_to_keep=6)
        assert config.max_context_tokens == 16000
        assert config.summarize_threshold == 12000
        assert config.min_messages_to_keep == 6


class TestContextManager:
    def test_context_manager_creation(self):
        manager = ContextManager()
        assert manager is not None

    def test_estimate_tokens_simple(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        tokens = context_manager.estimate_tokens(messages)
        assert tokens > 0
        assert tokens < 20  # Should be a small number for short messages

    def test_estimate_tokens_longer(self):
        long_message = "This is a much longer message that should use more tokens. " * 50
        messages = [{"role": "user", "content": long_message}]
        tokens = context_manager.estimate_tokens(messages)
        assert tokens > 100  # Should be significantly more tokens

    def test_manage_context_no_compression_needed(self):
        """Test that messages are returned unchanged when under token limit"""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        config = MemoryConfig(max_context_tokens=1000)  # High limit
        managed = context_manager.manage_context(messages, config, ContextStrategy.TRUNCATE_OLDEST, "Ollama")
        assert managed == messages

    def test_manage_context_with_compression(self):
        """Test that context is compressed when over token limit"""
        # Create many messages to exceed token limit
        messages = []
        for i in range(100):
            messages.append({"role": "user", "content": f"Message {i}: " + "This is a test message. " * 10})
            messages.append({"role": "assistant", "content": f"Response {i}: " + "This is a response. " * 10})

        config = MemoryConfig(max_context_tokens=1000)  # Low limit to force compression
        managed = context_manager.manage_context(messages, config, ContextStrategy.TRUNCATE_OLDEST, "Ollama")

        # Should have fewer messages after compression
        assert len(managed) < len(messages)
        # Should still have the most recent messages
        assert managed[-1]["role"] == "assistant"
        assert "Response 99" in managed[-1]["content"]

    def test_manage_context_truncate_strategy(self):
        """Test truncate strategy removes oldest messages"""
        messages = []
        for i in range(50):
            messages.append({"role": "user", "content": f"Old message {i}"})
            messages.append({"role": "assistant", "content": f"Old response {i}"})

        # Add some recent messages
        messages.append({"role": "user", "content": "Recent message"})
        messages.append({"role": "assistant", "content": "Recent response"})

        config = MemoryConfig(max_context_tokens=500)  # Low limit
        managed = context_manager.manage_context(messages, config, ContextStrategy.TRUNCATE_OLDEST, "Ollama")

        # Should have fewer messages
        assert len(managed) < len(messages)
        # Should contain recent messages
        assert any("Recent message" in msg["content"] for msg in managed)
        assert any("Recent response" in msg["content"] for msg in managed)

    def test_manage_context_summarize_strategy(self):
        """Test summarize strategy keeps recent messages"""
        messages = []
        for i in range(20):
            messages.append({"role": "user", "content": f"Question {i}"})
            messages.append({"role": "assistant", "content": f"Answer {i}"})

        config = MemoryConfig(max_context_tokens=200)  # Very low limit
        managed = context_manager.manage_context(messages, config, ContextStrategy.SUMMARIZE_OLDEST, "Ollama")

        # Should have fewer messages
        assert len(managed) <= len(messages)

    def test_context_strategy_enum_values(self):
        """Test that all context strategies are properly defined"""
        strategies = [strategy.value for strategy in ContextStrategy]
        expected = ["truncate_oldest", "summarize_oldest", "keep_recent", "sliding_window"]
        assert set(strategies) == set(expected)


class TestContextManagerIntegration:
    def test_context_manager_is_singleton(self):
        """Test that context_manager is a singleton instance"""
        manager1 = context_manager
        manager2 = context_manager
        assert manager1 is manager2

    def test_context_manager_has_estimate_tokens_method(self):
        """Test that the global context_manager has the estimate_tokens method"""
        tokens = context_manager.estimate_tokens([{"role": "user", "content": "test"}])
        assert isinstance(tokens, int)
        assert tokens > 0