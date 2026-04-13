"""Repository domain module."""

from abc import ABC, abstractmethod
from typing import Any


class SemanticMemoryStore(ABC):
    """Interface for Semantic Memory (Long-term Knowledge Base).

    Usually implemented by Vector Stores (Qdrant, Pinecone).
    """

    @abstractmethod
    def search_knowledge_base(
        self,
        query_text: str,
        tenant_id: str,
        limit: int = 5,
        filters: dict[str, Any] | None = None,
        scope_options: dict[str, Any] | None = None,
    ) -> str | list[dict]:
        """Retrieve relevant context from the knowledge base."""

    @abstractmethod
    def add_texts(
        self,
        texts: list[str],
        metadatas: list[dict],
        collection_name: str,
    ) -> None:
        """Add new knowledge to the memory."""


class EpisodicMemoryStore(ABC):
    """Interface for Episodic Memory (Short-term / Session History).

    Usually implemented by SQL (Postgres) or NoSQL (Mongo/Redis).
    """

    @abstractmethod
    def get_chat_history(self, user_id: str, limit: int = 10) -> list[Any]:
        """Retrieve recent conversation history for context window."""

    @abstractmethod
    def log_message(
        self,
        user_id: str,
        role: str,
        content: str,
        channel: str,
        tenant_id: str | None = None,
    ) -> Any:  # noqa: ANN401 — return type varies by implementation
        """Store a new message in the episode."""

    @abstractmethod
    def get_last_message(self, user_id: str) -> Any:  # noqa: ANN401 — return type varies by implementation
        """Retrieve the most recent message."""
