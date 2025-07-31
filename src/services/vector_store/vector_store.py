# src/services/vector_store.py
"""
Backward compatibility module for vector store functionality.
This module imports all classes from the refactored vector_store package.
"""

# Import all classes for backward compatibility
from .vector_store.base import VectorStore
from .vector_store.chroma_store import ChromaVectorStore
from .vector_store.search_service import VectorSearchService
from .vector_store.factory import VectorStoreFactory

# Keep all imports available at module level for existing code
__all__ = [
    "VectorStore",
    "ChromaVectorStore",
    "VectorSearchService",
    "VectorStoreFactory",
]
