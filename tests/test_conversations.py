"""
Tests for conversation management.
"""
import pytest
import json
import tempfile
from datetime import datetime
from conversations import Conversation, ConversationMessage, ConversationManager


class TestConversationMessage:
    """Tests for ConversationMessage."""

    def test_message_creation(self):
        """Test creating a message."""
        msg = ConversationMessage(
            role="user",
            content="Hello world",
            timestamp="2024-01-01T12:00:00",
            avatar="👤"
        )
        assert msg.role == "user"
        assert msg.content == "Hello world"
        assert msg.timestamp == "2024-01-01T12:00:00"
        assert msg.avatar == "👤"

    def test_message_to_dict(self):
        """Test converting message to dict."""
        msg = ConversationMessage(
            role="assistant",
            content="Hi there!",
            timestamp="2024-01-01T12:00:00"
        )
        data = msg.to_dict()
        assert data["role"] == "assistant"
        assert data["content"] == "Hi there!"
        assert data["timestamp"] == "2024-01-01T12:00:00"
        assert data["avatar"] is None

    def test_message_from_dict(self):
        """Test creating message from dict."""
        data = {
            "role": "user",
            "content": "Test message",
            "timestamp": "2024-01-01T12:00:00",
            "avatar": "🤖"
        }
        msg = ConversationMessage.from_dict(data)
        assert msg.role == "user"
        assert msg.content == "Test message"
        assert msg.timestamp == "2024-01-01T12:00:00"
        assert msg.avatar == "🤖"


class TestConversation:
    """Tests for Conversation."""

    def test_conversation_creation(self):
        """Test creating a new conversation."""
        conv = Conversation.new(
            persona_name="Test Mage",
            persona_class="Mage",
            persona_spec="Fire",
            provider_name="Ollama",
            model_name="llama3.2"
        )

        assert conv.persona_name == "Test Mage"
        assert conv.persona_class == "Mage"
        assert conv.persona_spec == "Fire"
        assert conv.provider_name == "Ollama"
        assert conv.model_name == "llama3.2"
        assert len(conv.messages) == 0
        assert conv.id.startswith("conv_")

    def test_conversation_with_custom_title(self):
        """Test creating conversation with custom title."""
        conv = Conversation.new(
            persona_name="Test Warrior",
            persona_class="Warrior",
            persona_spec="Arms",
            provider_name="OpenAI",
            model_name="gpt-4",
            title="Custom Title"
        )

        assert conv.title == "Custom Title"

    def test_add_message(self):
        """Test adding messages to conversation."""
        conv = Conversation.new(
            persona_name="Test",
            persona_class="Test",
            persona_spec="Test",
            provider_name="Test",
            model_name="Test"
        )

        conv.add_message("user", "Hello", "👤")
        conv.add_message("assistant", "Hi there!", "🤖")

        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[0].content == "Hello"
        assert conv.messages[0].avatar == "👤"
        assert conv.messages[1].role == "assistant"
        assert conv.messages[1].content == "Hi there!"
        assert conv.messages[1].avatar == "🤖"

    def test_get_messages_for_chat(self):
        """Test getting messages in chat format."""
        conv = Conversation.new(
            persona_name="Test",
            persona_class="Test",
            persona_spec="Test",
            provider_name="Test",
            model_name="Test"
        )

        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi!")

        chat_messages = conv.get_messages_for_chat()
        assert len(chat_messages) == 2
        assert chat_messages[0] == {"role": "user", "content": "Hello"}
        assert chat_messages[1] == {"role": "assistant", "content": "Hi!"}

    def test_conversation_to_dict(self):
        """Test converting conversation to dict."""
        conv = Conversation.new(
            persona_name="Test",
            persona_class="Test",
            persona_spec="Test",
            provider_name="Test",
            model_name="Test"
        )
        conv.add_message("user", "Test message")

        data = conv.to_dict()
        assert data["persona_name"] == "Test"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Test message"

    def test_conversation_from_dict(self):
        """Test creating conversation from dict."""
        data = {
            "id": "test_id",
            "title": "Test Conversation",
            "persona_name": "Test Persona",
            "persona_class": "Mage",
            "persona_spec": "Fire",
            "provider_name": "Ollama",
            "model_name": "llama3.2",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:30:00",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2024-01-01T12:00:00",
                    "avatar": "👤"
                }
            ],
            "tags": ["test"]
        }

        conv = Conversation.from_dict(data)
        assert conv.id == "test_id"
        assert conv.title == "Test Conversation"
        assert conv.persona_name == "Test Persona"
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello"

    def test_get_summary(self):
        """Test getting conversation summary."""
        conv = Conversation.new(
            persona_name="Test",
            persona_class="Test",
            persona_spec="Test",
            provider_name="Test",
            model_name="Test"
        )

        # Empty conversation
        assert conv.get_summary() == "Empty conversation"

        # Add messages
        conv.add_message("user", "Question 1")
        conv.add_message("assistant", "Answer 1")
        conv.add_message("user", "Question 2")

        summary = conv.get_summary()
        assert "2 questions" in summary
        assert "1 responses" in summary


class TestConversationManager:
    """Tests for ConversationManager."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ConversationManager(self.temp_dir)

    def test_save_and_load_conversation(self):
        """Test saving and loading conversations."""
        conv = Conversation.new(
            persona_name="Test Persona",
            persona_class="Mage",
            persona_spec="Fire",
            provider_name="Ollama",
            model_name="llama3.2"
        )
        conv.add_message("user", "Hello")
        conv.add_message("assistant", "Hi there!")

        # Save conversation
        filepath = self.manager.save_conversation(conv)
        assert filepath.endswith(f"{conv.id}.json")

        # Load conversation
        loaded_conv = self.manager.load_conversation(conv.id)
        assert loaded_conv is not None
        assert loaded_conv.id == conv.id
        assert loaded_conv.persona_name == "Test Persona"
        assert len(loaded_conv.messages) == 2

    def test_list_conversations(self):
        """Test listing conversations."""
        import time

        # Create multiple conversations with slight delays
        conv1 = Conversation.new("Persona1", "Mage", "Fire", "Ollama", "llama3.2")
        time.sleep(0.01)  # Small delay to ensure different timestamps
        conv2 = Conversation.new("Persona2", "Warrior", "Arms", "OpenAI", "gpt-4")

        self.manager.save_conversation(conv1)
        self.manager.save_conversation(conv2)

        conversations = self.manager.list_conversations()
        assert len(conversations) == 2

        # Should be sorted by updated_at descending
        assert conversations[0].persona_name == "Persona2"
        assert conversations[1].persona_name == "Persona1"

    def test_delete_conversation(self):
        """Test deleting conversations."""
        conv = Conversation.new("Test", "Test", "Test", "Test", "Test")
        self.manager.save_conversation(conv)

        # Verify it exists
        assert self.manager.load_conversation(conv.id) is not None

        # Delete it
        assert self.manager.delete_conversation(conv.id) is True

        # Verify it's gone
        assert self.manager.load_conversation(conv.id) is None

        # Try to delete non-existent
        assert self.manager.delete_conversation("nonexistent") is False

    def test_export_formats(self):
        """Test exporting conversations in different formats."""
        conv = Conversation.new(
            persona_name="Test Mage",
            persona_class="Mage",
            persona_spec="Fire",
            provider_name="Ollama",
            model_name="llama3.2",
            title="Test Conversation"
        )
        conv.add_message("user", "Hello world", "👤")
        conv.add_message("assistant", "Hi there!", "🧙‍♂️")

        self.manager.save_conversation(conv)

        # Test JSON export
        json_export = self.manager.export_conversation(conv.id, "json")
        assert json_export is not None
        json_data = json.loads(json_export)
        assert json_data["title"] == "Test Conversation"

        # Test text export
        txt_export = self.manager.export_conversation(conv.id, "txt")
        assert txt_export is not None
        assert "Test Conversation" in txt_export
        assert "Hello world" in txt_export
        assert "Hi there!" in txt_export

        # Test markdown export
        md_export = self.manager.export_conversation(conv.id, "markdown")
        assert md_export is not None
        assert "# Test Conversation" in md_export
        assert "**👤 User:** Hello world" in md_export
        assert "**🧙‍♂️ Assistant:** Hi there!" in md_export