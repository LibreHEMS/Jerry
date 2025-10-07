"""
Data models for Jerry Self-Hosted AI Migration.

This module contains the core data models representing users, conversations,
messages, and knowledge chunks for the Jerry AI assistant.
"""

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID
from uuid import uuid4


class ConversationStatus(Enum):
    """Status of a conversation."""

    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class MessageRole(Enum):
    """Role of a message in a conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class User:
    """Represents a Discord user interacting with Jerry."""

    discord_id: str
    username: str
    display_name: str
    first_interaction: datetime
    last_interaction: datetime
    preferences: dict[str, Any] = field(default_factory=dict)
    conversation_count: int = 0

    def __post_init__(self):
        """Validate user data after initialization."""
        if not self.discord_id:
            raise ValueError("discord_id must be non-empty")
        if not self.username:
            raise ValueError("username must be non-empty")


@dataclass
class Conversation:
    """Represents a conversation session between user and Jerry."""

    id: UUID
    user_discord_id: str
    channel_id: str
    started_at: datetime
    last_message_at: datetime
    status: ConversationStatus = ConversationStatus.ACTIVE
    context_summary: str = ""
    message_count: int = 0
    total_tokens_used: int = 0

    @classmethod
    def create_new(cls, user_discord_id: str, channel_id: str) -> "Conversation":
        """Create a new conversation instance."""
        now = datetime.utcnow()
        return cls(
            id=uuid4(),
            user_discord_id=user_discord_id,
            channel_id=channel_id,
            started_at=now,
            last_message_at=now,
        )

    def add_message_stats(self, tokens_used: int) -> None:
        """Update conversation statistics when a message is added."""
        self.message_count += 1
        self.total_tokens_used += tokens_used
        self.last_message_at = datetime.utcnow()


@dataclass
class Message:
    """Individual messages within a conversation."""

    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    timestamp: datetime
    tokens_used: int = 0
    response_time_ms: int = 0
    model_used: str = ""
    tools_used: list[str] = field(default_factory=list)
    rag_sources: list[str] = field(default_factory=list)


@dataclass
class CacheEntry:
    """Represents a generic cache entry for key-value caching."""

    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime | None = None

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return self.expires_at is not None and datetime.utcnow() > self.expires_at


@dataclass
class KnowledgeChunk:
    """Represents chunks of knowledge base documents for RAG."""

    id: UUID
    document_id: str
    title: str
    content: str
    embedding: list[float]
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    chunk_index: int = 0
    relevance_score: float = 0.0

    @classmethod
    def create_from_document(
        cls,
        document_id: str,
        title: str,
        content: str,
        chunk_index: int,
        metadata: dict[str, Any] | None = None,
    ) -> "KnowledgeChunk":
        """Create a new knowledge chunk from document content."""
        now = datetime.utcnow()
        return cls(
            id=uuid4(),
            document_id=document_id,
            title=title,
            content=content,
            embedding=[],  # Will be populated by embeddings service
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
            chunk_index=chunk_index,
        )

    def update_embedding(self, embedding: list[float]) -> None:
        """Update the embedding vector for this chunk."""
        self.embedding = embedding
        self.updated_at = datetime.utcnow()

    def __post_init__(self):
        """Validate knowledge chunk data after initialization."""
        if not self.document_id:
            raise ValueError("document_id must be non-empty")
        if not self.content:
            raise ValueError("content must be non-empty")
        if self.chunk_index < 0:
            raise ValueError("chunk_index must be non-negative")
