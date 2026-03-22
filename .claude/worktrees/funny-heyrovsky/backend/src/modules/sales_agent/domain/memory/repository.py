from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Union

class SemanticMemoryStore(ABC):
    """
    Interface for Semantic Memory (Long-term Knowledge Base).
    Usually implemented by Vector Stores (Qdrant, Pinecone).
    """
    
    @abstractmethod
    def search_knowledge_base(
        self, 
        query_text: str, 
        tenant_id: str, 
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        scope_options: Optional[Dict[str, Any]] = None
    ) -> Union[str, List[Dict]]:
        """
        Retrieve relevant context from the knowledge base.
        """
        pass

    @abstractmethod
    def add_texts(
        self, 
        texts: List[str], 
        metadatas: List[dict], 
        collection_name: str
    ) -> None:
        """
        Add new knowledge to the memory.
        """
        pass

class EpisodicMemoryStore(ABC):
    """
    Interface for Episodic Memory (Short-term / Session History).
    Usually implemented by SQL (Postgres) or NoSQL (Mongo/Redis).
    """

    @abstractmethod
    def get_chat_history(self, user_id: str, limit: int = 10) -> List[Any]:
        """
        Retrieve recent conversation history for context window.
        """
        pass

    @abstractmethod
    def log_message(self, user_id: str, role: str, content: str, channel: str, tenant_id: Optional[str] = None) -> Any:
        """
        Store a new message in the episode.
        """
        pass

    @abstractmethod
    def get_last_message(self, user_id: str) -> Any:
        """
        Retrieve the most recent message.
        """
        pass
