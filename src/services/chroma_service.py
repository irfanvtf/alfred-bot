import logging
from typing import List, Dict, Any
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

logger = logging.getLogger(__name__)

class ChromaService:
    """Service for managing ChromaDB operations."""

    def __init__(self, chroma_client: chromadb.Client):
        """
        Initializes the ChromaService.

        Args:
            chroma_client: An instance of the ChromaDB client.
        """
        self.client = chroma_client

    def initialize_embedding_function(self) -> None:
        """
        This method is kept for interface compatibility but doesn't need to do anything
        since embeddings are handled per collection.
        """
        logger.info("ChromaService: Embedding function initialization skipped - handled per collection")

    def list_collections(self) -> List[Dict[str, Any]]:
        """
        Lists all collections in ChromaDB.

        Returns:
            A list of collection objects.
        """
        try:
            collections = self.client.list_collections()
            return [{"name": col.name, "metadata": col.metadata} for col in collections]
        except Exception as e:
            logger.error(f"Failed to list ChromaDB collections: {e}", exc_info=True)
            raise

    def query_collection(self, collection_name: str, query_texts: List[str], n_results: int = 10, where_filter: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Queries a specific collection in ChromaDB.

        Args:
            collection_name: The name of the collection to query.
            query_texts: The texts to query for.
            n_results: The number of results to return.
            where_filter: A filter to apply to the query.

        Returns:
            The query results.
        """
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

