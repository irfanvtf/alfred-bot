# src/services/vector_store/chroma_store.py
from typing import List, Dict, Any, Optional
from .base import VectorStore
from src.utils.exceptions import ConfigurationError

# Import for Chroma (add to requirements.txt: chromadb)
try:
    import chromadb
    from chromadb.config import Settings

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False


class ChromaVectorStore(VectorStore):
    """Chroma implementation for development/prototyping"""

    def __init__(
        self,
        collection_name: str = "alfred_knowledge",
        persist_path: str = "./data/chroma_db",
    ):
        self.collection_name = collection_name
        self.persist_path = persist_path
        self.client = None
        self.collection = None

    def initialize(self) -> None:
        """Initialize Chroma client and collection"""
        if not CHROMA_AVAILABLE:
            raise ConfigurationError(
                "chromadb not installed. Run: pip install chromadb"
            )

        try:
            # Initialize Chroma client (persistent storage)
            self.client = chromadb.PersistentClient(
                path="./data/chroma_db", settings=Settings(anonymized_telemetry=False)
            )

            # Create or get collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Alfred Bot Knowledge Base"},
            )

            print(f"✅ Chroma initialized with collection: {self.collection_name}")

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Chroma: {e}") from e

    def add_vectors(self, vectors: List[Dict[str, Any]]) -> None:
        """Add vectors to Chroma collection"""
        if not self.collection:
            self.initialize()

        try:
            ids = [v["id"] for v in vectors]
            embeddings = [v["vector"] for v in vectors]
            metadatas = [v["metadata"] for v in vectors]
            documents = [v["text"] for v in vectors]

            self.collection.add(
                ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents
            )

            print(f"✅ Added {len(vectors)} vectors to Chroma")

        except Exception as e:
            raise ConfigurationError(f"Failed to add vectors to Chroma: {e}") from e

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search Chroma collection"""
        if not self.collection:
            self.initialize()

        try:
            # Build where clause for filtering
            where_clause = None
            if filters:
                where_clause = {}
                for key, value in filters.items():
                    where_clause[key] = {"$eq": value}

            results = self.collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            # Format results
            formatted_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    formatted_results.append(
                        {
                            "id": results["ids"][0][i],
                            "text": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "score": 1
                            - results["distances"][0][
                                i
                            ],  # Convert distance to similarity
                            "distance": results["distances"][0][i],
                        }
                    )

            return formatted_results

        except Exception as e:
            raise ConfigurationError(f"Failed to search Chroma: {e}") from e

    def delete_vectors(self, ids: List[str]) -> None:
        """Delete vectors from Chroma"""
        if not self.collection:
            self.initialize()

        try:
            self.collection.delete(ids=ids)
            print(f"✅ Deleted {len(ids)} vectors from Chroma")

        except Exception as e:
            raise ConfigurationError(
                f"Failed to delete vectors from Chroma: {e}"
            ) from e

    def get_stats(self) -> Dict[str, Any]:
        """Get Chroma collection statistics"""
        if not self.collection:
            self.initialize()

        try:
            count = self.collection.count()
            return {
                "store_type": "chroma",
                "collection_name": self.collection_name,
                "vector_count": count,
                "status": "connected",
            }
        except Exception as e:
            return {
                "store_type": "chroma",
                "collection_name": self.collection_name,
                "vector_count": 0,
                "status": f"error: {e}",
            }
