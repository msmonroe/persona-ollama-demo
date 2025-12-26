"""
Conversation management for the persona chat app.
"""
from __future__ import annotations
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class ConversationMessage:
    """A single message in a conversation."""
    role: str
    content: str
    timestamp: str
    avatar: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConversationMessage:
        """Create a message from a dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
            avatar=data.get("avatar")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return asdict(self)


@dataclass
class Conversation:
    """A conversation with metadata and messages."""
    id: str
    title: str
    persona_name: str
    persona_class: str
    persona_spec: str
    provider_name: str
    model_name: str
    created_at: str
    updated_at: str
    messages: List[ConversationMessage]
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    @classmethod
    def new(
        cls,
        persona_name: str,
        persona_class: str,
        persona_spec: str,
        provider_name: str,
        model_name: str,
        title: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation."""
        now = datetime.now()
        now_iso = now.isoformat()
        # Use microseconds for unique ID
        conversation_id = f"conv_{int(now.timestamp() * 1000000)}"

        if not title:
            title = f"Chat with {persona_name} ({now_iso[:19]})"

        return cls(
            id=conversation_id,
            title=title,
            persona_name=persona_name,
            persona_class=persona_class,
            persona_spec=persona_spec,
            provider_name=provider_name,
            model_name=model_name,
            created_at=now_iso,
            updated_at=now_iso,
            messages=[]
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Conversation:
        """Create a conversation from a dictionary."""
        messages = [ConversationMessage.from_dict(msg) for msg in data["messages"]]
        return cls(
            id=data["id"],
            title=data["title"],
            persona_name=data["persona_name"],
            persona_class=data["persona_class"],
            persona_spec=data["persona_spec"],
            provider_name=data["provider_name"],
            model_name=data["model_name"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            messages=messages,
            tags=data.get("tags", [])
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to dictionary."""
        data = asdict(self)
        data["messages"] = [msg.to_dict() for msg in self.messages]
        return data

    def add_message(self, role: str, content: str, avatar: Optional[str] = None):
        """Add a message to the conversation."""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            avatar=avatar
        )
        self.messages.append(message)
        self.updated_at = datetime.now().isoformat()

    def get_messages_for_chat(self) -> List[Dict[str, str]]:
        """Get messages in the format expected by chat functions."""
        return [{"role": msg.role, "content": msg.content} for msg in self.messages]

    def get_summary(self) -> str:
        """Get a summary of the conversation."""
        if not self.messages:
            return "Empty conversation"

        user_msgs = [msg for msg in self.messages if msg.role == "user"]
        assistant_msgs = [msg for msg in self.messages if msg.role == "assistant"]

        return f"{len(user_msgs)} questions, {len(assistant_msgs)} responses"


class ConversationManager:
    """Manages conversation storage and retrieval."""

    def __init__(self, conversations_dir: str = "saved_conversations"):
        self.conversations_dir = Path(conversations_dir)
        self.conversations_dir.mkdir(exist_ok=True)

    def save_conversation(self, conversation: Conversation) -> str:
        """Save a conversation to disk."""
        filepath = self.conversations_dir / f"{conversation.id}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation.to_dict(), f, indent=2, ensure_ascii=False)
        return str(filepath)

    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Load a conversation from disk."""
        filepath = self.conversations_dir / f"{conversation_id}.json"
        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Conversation.from_dict(data)
        except Exception:
            return None

    def list_conversations(self) -> List[Conversation]:
        """List all saved conversations."""
        conversations = []
        for filepath in self.conversations_dir.glob("*.json"):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                conversations.append(Conversation.from_dict(data))
            except Exception:
                continue

        # Sort by updated_at descending
        conversations.sort(key=lambda c: c.updated_at, reverse=True)
        return conversations

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        filepath = self.conversations_dir / f"{conversation_id}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def export_conversation(self, conversation_id: str, format: str = "json") -> Optional[str]:
        """Export a conversation in the specified format."""
        conversation = self.load_conversation(conversation_id)
        if not conversation:
            return None

        if format == "json":
            return json.dumps(conversation.to_dict(), indent=2, ensure_ascii=False)
        elif format == "txt":
            lines = [f"Conversation: {conversation.title}"]
            lines.append(f"Persona: {conversation.persona_name} ({conversation.persona_class}/{conversation.persona_spec})")
            lines.append(f"Model: {conversation.provider_name} - {conversation.model_name}")
            lines.append(f"Created: {conversation.created_at}")
            lines.append("")
            lines.append("Messages:")
            lines.append("-" * 50)

            for msg in conversation.messages:
                timestamp = msg.timestamp[:19] if msg.timestamp else ""
                avatar = msg.avatar or ("🤖" if msg.role == "assistant" else "👤")
                lines.append(f"[{timestamp}] {avatar} {msg.role.title()}: {msg.content}")
                lines.append("")

            return "\n".join(lines)
        elif format == "markdown":
            lines = [f"# {conversation.title}"]
            lines.append("")
            lines.append(f"**Persona:** {conversation.persona_name} ({conversation.persona_class}/{conversation.persona_spec})")
            lines.append(f"**Model:** {conversation.provider_name} - {conversation.model_name}")
            lines.append(f"**Created:** {conversation.created_at}")
            lines.append("")
            lines.append("## Messages")
            lines.append("")

            for msg in conversation.messages:
                avatar = msg.avatar or ("🤖" if msg.role == "assistant" else "👤")
                lines.append(f"**{avatar} {msg.role.title()}:** {msg.content}")
                lines.append("")

            return "\n".join(lines)

        return None