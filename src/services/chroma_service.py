import logging
from typing import List, Dict, Any
import chromadb

logger = logging.getLogger(__name__)

class ChromaService:
    """Service for managing ChromaDB operations."""

    def __init__(self, chroma_client: chromadb.Client):
        """Initializes the ChromaService."""
        self.client = chroma_client

    

    def list_collections(self) -> List[Dict[str, Any]]:
        """Lists all collections in ChromaDB."""
        try:
            collections = self.client.list_collections()
            return [{"name": col.name, "metadata": col.metadata} for col in collections]
        except Exception as e:
            logger.error(f"Failed to list ChromaDB collections: {e}", exc_info=True)
            raise

    def query_collection(self, collection_name: str, query_texts: List[str], n_results: int = 10, where_filter: Dict[str, Any] = None) -> Dict[str, Any]:
        """Queries a specific collection in ChromaDB."""
        try:
            collection = self.client.get_collection(name=collection_name)
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query collection {collection_name}: {e}", exc_info=True)
            raise

