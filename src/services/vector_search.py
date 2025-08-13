# src/services/vector_store/search_service.py
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from src.utils.exceptions import ConfigurationError
from src.services.text_processor import text_processor

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.api.models.Collection import Collection
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for managing vector operations with session context across multiple collections"""

    def __init__(
        self,
        persist_path: str = "./data/chroma_db",
    ):
        self.text_processor = text_processor
        self.confidence_threshold = 0.6
        self.persist_path = persist_path
        self.client: Optional[chromadb.Client] = None

    def initialize(self) -> None:
        """Initialize Chroma client (collections managed dynamically)"""
        if not CHROMA_AVAILABLE:
            raise ConfigurationError(
                "chromadb not installed. Run: pip install chromadb"
            )

        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    chroma_client_auth_provider="",
                    chroma_server_host="",
                ),
            )

            logger.info(
                f"Chroma client initialized with persist path: {self.persist_path}"
            )

        except Exception as e:
            raise ConfigurationError(f"Failed to initialize Chroma client: {e}") from e

    def _ensure_client(self) -> None:
        """Ensure the Chroma client is initialized."""
        if self.client is None:
            self.initialize()

    def _get_or_create_collection(
        self,
        collection_name: str,
        description: str = "Alfred Bot Knowledge Base",
        language: Optional[str] = None,
    ) -> Collection:
        """Get or create a Chroma collection with language metadata."""
        self._ensure_client()

        metadata = {"description": description}
        if language:
            metadata["language"] = language
            if not language and collection_name.startswith("intent_"):
                metadata["language"] = collection_name.split("_", 1)[1]
            elif not language:
                parts = collection_name.split("_")
                if len(parts) > 1:
                    metadata["language"] = parts[-1]

        embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=self.text_processor.bert_model_name
        )

        collection: Collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata=metadata,
            embedding_function=embedding_function,
        )

        return collection

    def _get_collection(self, collection_name: str) -> Collection:
        """Get an existing Chroma collection."""
        self._ensure_client()
        return self.client.get_collection(name=collection_name)

    def add_vectors(
        self,
        collection_name: str,
        vectors: List[Dict[str, Any]],
        language: Optional[str] = None,
    ) -> None:
        """Add vectors to a specific Chroma collection"""
        if not vectors:
            print("⚠️ No vectors provided to add.")
            return

        try:
            collection = self._get_or_create_collection(
                collection_name,
                f"Alfred Bot Knowledge Base - {collection_name}",
                language,
            )

            ids = [v["id"] for v in vectors]
            embeddings = [v["vector"] for v in vectors]
            metadatas = [v["metadata"] for v in vectors]
            documents = [v["text"] for v in vectors]

            logger.info(
                f"Adding {len(vectors)} vectors to collection '{collection_name}'"
            )

            collection.add(
                ids=ids, embeddings=embeddings, metadatas=metadatas, documents=documents
            )

            logger.info(
                f"Added {len(vectors)} vectors to Chroma collection '{collection_name}'"
            )

        except Exception as e:
            raise ConfigurationError(
                f"Failed to add vectors to Chroma collection '{collection_name}': {e}"
            ) from e

    def search_collection(
        self,
        collection_name: str,
        query_vector: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        language: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search a specific Chroma collection"""
        try:
            collection = self._get_collection(collection_name)

            where_clause = filters if filters else None
            if language:
                if where_clause is None:
                    where_clause = {}
                where_clause["source_language"] = {"$eq": language}

            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
                where=where_clause,
                include=["documents", "metadatas", "distances"],
            )

            formatted_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    distance = results["distances"][0][i]
                    similarity = max(0.0, 1.0 - (distance / 2.0))

                    formatted_results.append(
                        {
                            "id": results["ids"][0][i],
                            "text": results["documents"][0][i],
                            "metadata": results["metadatas"][0][i],
                            "score": similarity,
                            "distance": distance,
                        }
                    )

            return formatted_results

        except Exception as e:
            logger.error(
                f"Error searching collection '{collection_name}': {e}", exc_info=True
            )
            raise ConfigurationError(
                f"Failed to search Chroma collection '{collection_name}': {e}"
            ) from e

    def get_stats(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """Get Chroma collection statistics. If no collection_name, returns client info."""
        self._ensure_client()
        try:
            if collection_name:
                collection = self._get_collection(collection_name)
                count = collection.count()
                return {
                    "store_type": "chroma",
                    "collection_name": collection_name,
                    "vector_count": count,
                    "status": "connected",
                }
            else:
                collections = self.client.list_collections()
                collection_names = [c.name for c in collections]
                return {
                    "store_type": "chroma",
                    "persist_path": self.persist_path,
                    "collections": collection_names,
                    "status": "connected",
                }
        except Exception as e:
            return {
                "store_type": "chroma",
                "collection_name": collection_name,
                "vector_count": 0,
                "status": f"error: {e}",
            }

    def get_collections_by_language(self, language: str) -> List[str]:
        """Get all collection names that match a specific language."""
        self._ensure_client()
        try:
            collections = self.client.list_collections()
            matching_collections = []

            for collection in collections:
                metadata = collection.metadata or {}
                if metadata.get("language") == language:
                    matching_collections.append(collection.name)
                elif collection.name.endswith(f"_{language}"):
                    matching_collections.append(collection.name)

            return matching_collections
        except Exception as e:
            logger.error(f"Error getting collections by language '{language}': {e}")
            return []

    def get_available_languages(self) -> List[str]:
        """Get all available languages from collections."""
        self._ensure_client()
        try:
            collections = self.client.list_collections()
            languages = set()

            for collection in collections:
                metadata = collection.metadata or {}
                if "language" in metadata:
                    languages.add(metadata["language"])
                elif collection.name.startswith("intent_"):
                    lang = collection.name.split("_", 1)[1]
                    languages.add(lang)
                elif "_" in collection.name:
                    parts = collection.name.split("_")
                    if len(parts) > 1:
                        languages.add(parts[-1])

            return list(languages)
        except Exception as e:
            logger.error(f"Error getting available languages: {e}")
            return []

    def index_knowledge_base(
        self,
        collection_name: str,
        knowledge_base_data: Dict[str, Any],
        source_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Index all intents from knowledge base into a specific collection."""
        vectors = []
        source_lang = (
            source_metadata.get("language", "unknown") if source_metadata else "unknown"
        )
        source_description = (
            source_metadata.get("description", "Unknown Source")
            if source_metadata
            else "Unknown Source"
        )

        for intent in knowledge_base_data.get("intents", []):
            intent_id = intent["id"]
            patterns = intent["patterns"]
            responses = intent["responses"]
            intent_metadata = intent.get("metadata", {})

            for i, pattern in enumerate(patterns):
                try:
                    processed = self.text_processor.preprocess_text(pattern)
                    vector = processed["vector"]

                    vector_metadata = {
                        "intent_id": intent_id,
                        "type": "pattern",
                        "category": intent_metadata.get("category", "general"),
                        "confidence_threshold": intent_metadata.get(
                            "confidence_threshold",
                            knowledge_base_data.get("metadata", {})
                            .get("search_config", {})
                            .get("default_confidence_threshold", 0.6),
                        ),
                        "responses": json.dumps(responses),
                        "original_text": pattern,
                        "processed_text": processed["cleaned"],
                        "keywords": json.dumps(processed.get("lemmas", [])[:5]),
                        "indexed_at": datetime.now().isoformat(),
                        "source_language": source_lang,
                        "source_collection": collection_name,
                        "intent_tags": json.dumps(intent_metadata.get("tags", [])),
                        "intent_priority": intent_metadata.get("priority", 1),
                    }

                    vector_entry = {
                        "id": f"{collection_name}_{intent_id}_pattern_{i}",
                        "vector": vector,
                        "text": pattern,
                        "metadata": vector_metadata,
                    }

                    vectors.append(vector_entry)

                except Exception as e:
                    print(
                        f"Error processing pattern '{pattern}' for intent '{intent_id}': {e}"
                    )
                    continue

        if vectors:
            self.add_vectors(collection_name, vectors, source_lang)
            logger.info(
                f"Indexed {len(vectors)} patterns into collection '{collection_name}' from source '{source_description}' (language: {source_lang})"
            )
        else:
            print(
                f"⚠️ No vectors created from knowledge base for collection '{collection_name}'"
            )

    def _determine_collection_for_search(
        self, session_context: Optional[Dict[str, Any]]
    ) -> str:
        """Determine the appropriate collection name based on session context."""
        if session_context:
            session_vars = session_context.get("context_variables", {})
            preferred_lang = session_vars.get("preferred_language")
            if preferred_lang:
                collection_name = f"intent_{preferred_lang}"
                logger.debug(
                    f"Using collection '{collection_name}' based on session context language '{preferred_lang}'"
                )
                return collection_name

        # Default to English if no language preference is found
        logger.info(
            "Could not determine specific language for search. Using default 'intent_en'."
        )
        return "intent_en"

    def search_intents(
        self,
        query: str,
        session_context: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        collection_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for matching intents with session context, determining the correct collection."""
        try:
            if collection_name:
                logger.debug(
                    f"Using explicit collection '{collection_name}' for query: {query[:50]}..."
                )
            else:
                collection_name = self._determine_collection_for_search(session_context)
                logger.debug(
                    f"Searching collection '{collection_name}' for query: {query[:50]}..."
                )

            enhanced_query = query
            cleaned_query = self.text_processor._clean_text(enhanced_query)
            query_vector = self.text_processor.get_text_vector(cleaned_query)
            filters = self._build_context_filters(session_context)

            results = self.search_collection(
                collection_name=collection_name,
                query_vector=query_vector,
                top_k=top_k,
                filters=filters,
                language=None,
            )

            filtered_results = []
            for result in results:
                score = result.get("score", 0)
                metadata = result.get("metadata", {})
                threshold = metadata.get(
                    "confidence_threshold", self.confidence_threshold
                )

                context_score = self._calculate_context_score(result, session_context)
                final_score = (score * 0.7) + (context_score * 0.3)
                result["final_score"] = final_score
                result["context_score"] = context_score
                result["original_score"] = score
                result["threshold"] = threshold

                filtered_results.append(result)

            filtered_results.sort(key=lambda x: x["final_score"], reverse=True)

            threshold_filtered_results = []
            for r in filtered_results:
                final_score = r.get("final_score", 0)
                threshold = r.get("threshold", self.confidence_threshold)
                if final_score >= threshold:
                    threshold_filtered_results.append(r)

            return threshold_filtered_results

        except Exception as e:
            logging.error(f"Error in search_intents: {e}", exc_info=True)
            if isinstance(e, ConfigurationError):
                raise
            return []

    def _build_context_filters(
        self, context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Build filters based on session context"""
        if not context:
            return None

        filters = {}
        last_intent = context.get("context_variables", {}).get("last_intent")
        if last_intent:
            pass

        return filters if filters else None

    def _calculate_context_score(
        self, result: Dict[str, Any], context: Optional[Dict[str, Any]]
    ) -> float:
        """Calculate context-aware score boost"""
        if not context:
            return 0.0

        score = 0.0
        metadata = result.get("metadata", {})
        context_vars = context.get("context_variables", {})
        last_category = context_vars.get("last_category")
        result_category = metadata.get("category")

        if last_category and result_category:
            if last_category == result_category:
                score += 0.2
            elif last_category in ["greeting", "farewell"] and result_category in [
                "help",
                "thanks",
            ]:
                score += 0.1

        last_intent = context_vars.get("last_intent")
        if last_intent and metadata.get("intent_id"):
            flow_patterns = {
                "greeting": ["help", "thanks"],
                "help": ["thanks", "goodbye"],
                "thanks": ["goodbye", "help"],
            }

            expected_intents = flow_patterns.get(last_intent, [])
            if metadata["intent_id"] in expected_intents:
                score += 0.15

        return min(score, 1.0)

    def get_service_stats(self) -> Dict[str, Any]:
        """Get vector search service statistics"""
        client_stats = self.get_stats()
        processor_stats = self.text_processor.get_model_info()

        return {
            "vector_store_client": client_stats,
            "text_processor": processor_stats,
            "service_config": {
                "confidence_threshold": self.confidence_threshold,
                "store_type": client_stats.get("store_type", "unknown"),
            },
        }


vector_search_service = VectorSearchService()
