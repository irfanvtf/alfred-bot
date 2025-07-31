# src/services/vector_store/search_service.py
import json
import random
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from src.utils.exceptions import ConfigurationError
from .chroma_store import ChromaVectorStore
from src.services.text_processor import TextProcessor

logger = logging.getLogger(__name__)


class VectorSearchService:
    """Service for managing vector operations with session context"""

    def __init__(self):
        self.text_processor = TextProcessor()
        self.vector_store = ChromaVectorStore()
        self.confidence_threshold = 0.5

    def initialize(self) -> None:
        """Initialize the vector search service"""
        self.vector_store.initialize()

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
            self.vector_store.add_vectors(vectors)
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
            results = self.vector_store.search(
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

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        store_stats = self.vector_store.get_stats()
        processor_stats = self.text_processor.get_model_info()

        return {
            "vector_store": store_stats,
            "text_processor": processor_stats,
            "service_config": {
                "confidence_threshold": self.confidence_threshold,
                "store_type": store_stats.get("store_type", "unknown"),
            },
        }
