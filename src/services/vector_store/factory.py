# src/services/vector_store/factory.py
"""Factory for creating vector store instances"""

from typing import Optional
from .base import VectorStore
from .chroma_store import ChromaVectorStore
from .pinecone_store import PineconeVectorStore
from src.utils.exceptions import ConfigurationError


class VectorStoreFactory:
    """Factory class for creating vector store instances"""

    @staticmethod
    def create_vector_store(store_type: str, **kwargs) -> VectorStore:
        """Create a vector store instance based on type

        Args:
            store_type: Type of vector store ('chroma' or 'pinecone')
            **kwargs: Additional arguments for store initialization

        Returns:
            VectorStore instance

        Raises:
            ConfigurationError: If store type is not supported
        """
        store_type = store_type.lower()

        if store_type == "chroma":
            collection_name = kwargs.get("collection_name", "alfred_knowledge")
            return ChromaVectorStore(collection_name=collection_name)

        elif store_type == "pinecone":
            index_name = kwargs.get("index_name", "alfred-knowledge")
            return PineconeVectorStore(index_name=index_name)

        else:
            raise ConfigurationError(
                f"Unsupported vector store type: {store_type}. "
                f"Supported types: chroma, pinecone"
            )

    @staticmethod
    def get_available_stores() -> list:
        """Get list of available vector store types"""
        return ["chroma", "pinecone"]
