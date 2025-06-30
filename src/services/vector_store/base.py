# src/services/vector_store/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorStore(ABC):
    """Abstract base class for vector stores"""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the vector store"""
        pass

    @abstractmethod
    def add_vectors(self, vectors: List[Dict[str, Any]]) -> None:
        """Add vectors to the store"""
        pass

    @abstractmethod
    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        pass

    @abstractmethod
    def delete_vectors(self, ids: List[str]) -> None:
        """Delete vectors by IDs"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics"""
        pass
