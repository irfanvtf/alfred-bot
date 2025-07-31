# src/services/vector_store/search_service.py
import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from src.utils.exceptions import ConfigurationError
from src.services.text_processor import TextProcessor

# Import for Chroma (add to requirements.txt: chromadb)
try:
    import chromadb
    from chromadb.config import Settings

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for managing vector operations with session context"""

    def __init__(
        self,
        collection_name: str = "alfred_knowledge",
        persist_path: str = "./data/chroma_db",
    ):
        self.text_processor = TextProcessor()
        self.confidence_threshold = 0.5
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
                path=self.persist_path, settings=Settings(anonymized_telemetry=False)
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
                    distance = results["distances"][0][i]
                    # For very high distances, use inverse relationship
                    # Temporarily use a more lenient scoring for testing
                    similarity = 1.0 / (
                        1.0 + distance / 5.0
                    )  # This will give values between 0-1

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

    def index_knowledge_base(self, knowledge_base_data: Dict[str, Any]) -> None:
        """Index all intents from knowledge base"""
        vectors = []

        for intent in knowledge_base_data.get("intents", []):
            intent_id = intent["id"]
            patterns = intent["patterns"]
            responses = intent["responses"]
            metadata = intent.get("metadata", {})

            # Create vectors for each pattern
            for i, pattern in enumerate(patterns):
                try:
                    # Process text and get vector
                    processed = self.text_processor.preprocess_text(pattern)
                    vector = processed["vector"]

                    # Create vector entry
                    vector_entry = {
                        "id": f"{intent_id}_pattern_{i}",
                        "vector": vector,
                        "text": pattern,
                        "metadata": {
                            "intent_id": intent_id,
                            "type": "pattern",
                            "category": metadata.get("category", "general"),
                            "confidence_threshold": metadata.get(
                                "confidence_threshold", 0.5
                            ),
                            "responses": json.dumps(responses),
                            "original_text": pattern,
                            "processed_text": processed["cleaned"],
                            "keywords": json.dumps(processed.get("lemmas", [])[:5]),
                            "indexed_at": datetime.now().isoformat(),
                        },
                    }

                    vectors.append(vector_entry)

                except Exception as e:
                    print(f"Error processing pattern '{pattern}': {e}")
                    continue

        # Add vectors to store
        if vectors:
            self.add_vectors(vectors)
            logger.info(f"Indexed {len(vectors)} patterns from knowledge base")
        else:
            print("⚠️ No vectors created from knowledge base")

    def search_intents(
        self,
        query: str,
        session_context: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search for matching intents with session context"""
        try:
            # Enhance query with session context
            enhanced_query = self._enhance_query_with_context(query, session_context)

            # Get query vector
            query_vector = self.text_processor.get_text_vector(enhanced_query)

            # Build filters based on session context
            filters = self._build_context_filters(session_context)

            # Search vector store (temporarily disable filters)
            results = self.search(
                query_vector=query_vector,
                top_k=top_k,
                filters=None,  # Temporarily disable filters
            )

            logger.debug(f"Search intents results: {results}")

            # Filter by confidence threshold and add context scoring
            filtered_results = []
            for result in results:
                score = result.get("score", 0)
                metadata = result.get("metadata", {})
                threshold = metadata.get(
                    "confidence_threshold", self.confidence_threshold
                )

                if score >= threshold:
                    # Add context-aware scoring
                    context_score = self._calculate_context_score(
                        result, session_context
                    )
                    result["final_score"] = (score * 0.7) + (context_score * 0.3)
                    result["context_score"] = context_score
                    filtered_results.append(result)

            # Sort by final score
            filtered_results.sort(key=lambda x: x["final_score"], reverse=True)

            return filtered_results

        except Exception as e:
            logging.error(f"Error in search_intents: {e}", exc_info=True)
            # Consider re-raising configuration errors
            if isinstance(e, ConfigurationError):
                raise
            return []

    def _enhance_query_with_context(
        self, query: str, context: Optional[Dict[str, Any]]
    ) -> str:
        """Enhance query with conversation context"""
        if not context:
            return query

        enhanced_query = query

        # Add recent conversation context
        history = context.get("conversation_history", [])
        if history:
            # Get last few user messages for context
            recent_messages = [
                msg["message"] for msg in history[-3:] if msg.get("role") == "user"
            ]
            if recent_messages:
                context_text = " ".join(recent_messages[-2:])  # Last 2 user messages
                enhanced_query = f"{context_text} {query}"

        # Add context variables as keywords
        context_vars = context.get("context_variables", {})
        if context_vars:
            for key, value in context_vars.items():
                if isinstance(value, str) and len(value) < 50:
                    enhanced_query = f"{enhanced_query} {value}"

        return enhanced_query

    def _build_context_filters(
        self, context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Build filters based on session context"""
        if not context:
            return None

        filters = {}

        # Filter by conversation state
        last_intent = context.get("context_variables", {}).get("last_intent")
        if last_intent:
            # Could implement intent-flow logic here
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

        # Boost score based on category consistency
        context_vars = context.get("context_variables", {})
        last_category = context_vars.get("last_category")
        result_category = metadata.get("category")

        if last_category and result_category:
            if last_category == result_category:
                score += 0.2  # Same category boost
            elif last_category in ["greeting", "farewell"] and result_category in [
                "help",
                "thanks",
            ]:
                score += 0.1  # Related category boost

        # Boost for conversation flow
        last_intent = context_vars.get("last_intent")
        if last_intent and metadata.get("intent_id"):
            # Define intent flow patterns
            flow_patterns = {
                "greeting": ["help", "thanks"],
                "help": ["thanks", "goodbye"],
                "thanks": ["goodbye", "help"],
            }

            expected_intents = flow_patterns.get(last_intent, [])
            if metadata["intent_id"] in expected_intents:
                score += 0.15

        return min(score, 1.0)  # Cap at 1.0

    def get_fallback_response(
        self, query: str, session_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate fallback response when no good matches found"""
        fallback_responses = [
            "I'm not sure I understand. Could you please rephrase that?",
            "I don't have information about that topic. Can you ask something else?",
            "That's not something I'm familiar with. How else can I help you?",
            "I'm still learning about that. Is there something else I can assist with?",
        ]

        # Choose response based on context
        response = random.choice(fallback_responses)

        return {
            "intent_id": "fallback",
            "response": response,
            "confidence": 0.0,
            "type": "fallback",
            "suggestions": [
                "Try asking about greetings, help, or thanks",
                "Be more specific in your question",
            ],
        }

    def get_service_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        store_stats = self.get_stats()
        processor_stats = self.text_processor.get_model_info()

        return {
            "vector_store": store_stats,
            "text_processor": processor_stats,
            "service_config": {
                "confidence_threshold": self.confidence_threshold,
                "store_type": store_stats.get("store_type", "unknown"),
            },
        }