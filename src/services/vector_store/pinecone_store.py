# src/services/vector_store/pinecone_store.py
from typing import List, Dict, Any, Optional
from .base import VectorStore
from src.utils.exceptions import ConfigurationError
from config.settings import settings

# Import for Pinecone (already in your requirements.txt)
try:
    from pinecone import Pinecone

    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False


class PineconeVectorStore(VectorStore):
    """Pinecone implementation for production"""

    def __init__(self, index_name: str = "alfred-knowledge"):
        self.index_name = index_name
        self.index = None

    def initialize(self) -> None:
        """Initialize Pinecone client and index"""
        if not PINECONE_AVAILABLE:
            raise ConfigurationError("pinecone-client not installed")

        try:
            # Instantiate the Pinecone client
            self.pc = Pinecone(
                api_key=settings.pinecone_api_key,
                environment=settings.pinecone_environment,
            )

            # Check if index exists, create if not
            if self.index_name not in self.pc.list_indexes():
                self.pc.create_index(
                    name=self.index_name,
                    dimension=300,  # spaCy medium model dimension
                    metric="cosine",
                )
                print(f"✅ Created Pinecone index: {self.index_name}")

            # Connect to index
            self.index = self.pc.Index(self.index_name)
            print(f"✅ Connected to Pinecone index: {self.index_name}")

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Pinecone: {e}") from e

    def add_vectors(self, vectors: List[Dict[str, Any]]) -> None:
        """Add vectors to Pinecone index"""
        if not self.index:
            self.initialize()

        try:
            # Format for Pinecone
            pinecone_vectors = []
            for v in vectors:
                pinecone_vectors.append(
                    {"id": v["id"], "values": v["vector"], "metadata": v["metadata"]}
                )

            # Upsert in batches
            batch_size = 100
            for i in range(0, len(pinecone_vectors), batch_size):
                batch = pinecone_vectors[i : i + batch_size]
                self.index.upsert(vectors=batch)

            print(f"✅ Added {len(vectors)} vectors to Pinecone")

        except Exception as e:
            raise ConfigurationError(f"Failed to add vectors to Pinecone: {e}") from e

    def search(
        self,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search Pinecone index"""
        if not self.index:
            self.initialize()

        try:
            results = self.index.query(
                vector=query_vector, top_k=top_k, filter=filters, include_metadata=True
            )

            # Format results
            formatted_results = []
            for match in results.matches:
                formatted_results.append(
                    {
                        "id": match.id,
                        "score": match.score,
                        "metadata": match.metadata,
                        "text": match.metadata.get("text", ""),
                    }
                )

            return formatted_results

        except Exception as e:
            raise ConfigurationError(f"Failed to search Pinecone: {e}") from e

    def delete_vectors(self, ids: List[str]) -> None:
        """Delete vectors from Pinecone"""
        if not self.index:
            self.initialize()

        try:
            self.index.delete(ids=ids)
            print(f"✅ Deleted {len(ids)} vectors from Pinecone")

        except Exception as e:
            raise ConfigurationError(
                f"Failed to delete vectors from Pinecone: {e}"
            ) from e

    def get_stats(self) -> Dict[str, Any]:
        """Get Pinecone index statistics"""
        if not self.index:
            self.initialize()

        try:
            stats = self.index.describe_index_stats()
            return {
                "store_type": "pinecone",
                "index_name": self.index_name,
                "vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "status": "connected",
            }
        except Exception as e:
            return {
                "store_type": "pinecone",
                "index_name": self.index_name,
                "vector_count": 0,
                "status": f"error: {e}",
            }
