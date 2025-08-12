# src/services/vector_store/search_service.py
import json
import random
import math
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from src.utils.exceptions import ConfigurationError
from src.services.text_processor import TextProcessor, text_processor

# Import for Chroma (add to requirements.txt: chromadb)
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.api.models.Collection import Collection  # For type hinting

    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)

class VectorSearchService:
    """Service for managing vector operations with session context across multiple collections"""

    def __init__(
        self,
        # collection_name: str = "alfred_knowledge", # Removed: Single collection focus
        persist_path: str = "./data/chroma_db",
    ):
        # Use the singleton text_processor instance to avoid loading the model multiple times
        self.text_processor = text_processor
        self.confidence_threshold = 0.6  # Standard confidence threshold
        # self.collection_name = collection_name # Removed: Single collection focus
        self.persist_path = persist_path
        self.client: Optional[chromadb.Client] = None
        # self.collection = None # Removed: Single collection focus

    def initialize(self) -> None:
        """Initialize Chroma client (collections managed dynamically)"""
        if not CHROMA_AVAILABLE:
            raise ConfigurationError(
                "chromadb not installed. Run: pip install chromadb"
            )

        try:
            # Initialize Chroma client (persistent storage)
            self.client = chromadb.PersistentClient(
                path=self.persist_path,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
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

        # Prepare metadata with language information
        metadata = {"description": description}
        if language:
            metadata["language"] = language
            # Extract language from collection name if not explicitly provided
            # This follows the pattern like 'intent_en' -> 'en'
            if not language and collection_name.startswith("intent_"):
                metadata["language"] = collection_name.split("_", 1)[1]
            elif not language:
                # Try to infer language from collection name
                parts = collection_name.split("_")
                if len(parts) > 1:
                    metadata["language"] = parts[-1]  # Last part as language code

        # Create the embedding function with the correct model
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,
        )

        embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=self.text_processor.bert_model_name
        )

        # Type hinting might be tricky without full import, but it's the correct type
        collection: Collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata=metadata,
            embedding_function=embedding_function,
        )

        return collection

    def _get_collection(self, collection_name: str) -> Collection:
        """Get an existing Chroma collection."""
        self._ensure_client()
        # Type hinting might be tricky without full import, but it's the correct type
        collection: Collection = self.client.get_collection(name=collection_name)
        return collection

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
            logger.debug(f"First vector ID: {ids[0] if ids else 'None'}")
            logger.debug(
                f"First vector text: {documents[0][:50] if documents and documents[0] else 'None'}"
            )
            logger.debug(
                f"First vector dimension: {len(embeddings[0]) if embeddings and embeddings[0] else 'None'}"
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

    def search(
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

            # Build where clause for filtering
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

            # Format results
            formatted_results = []
            if results["ids"] and len(results["ids"][0]) > 0:
                for i in range(len(results["ids"][0])):
                    distance = results["distances"][0][i]

                    # Convert distance to similarity score (0-1 range)
                    # For cosine distance, similarity = 1 - (distance / 2)
                    # This is the standard conversion for cosine distance which ranges from 0-2
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

    def delete_vectors(self, collection_name: str, ids: List[str]) -> None:
        """Delete vectors from a specific Chroma collection"""
        if not ids:
            print("⚠️ No vector IDs provided to delete.")
            return

        try:
            collection = self._get_collection(collection_name)
            collection.delete(ids=ids)
            logger.info(
                f"Deleted {len(ids)} vectors from Chroma collection '{collection_name}'"
            )

        except Exception as e:
            raise ConfigurationError(
                f"Failed to delete vectors from Chroma collection '{collection_name}': {e}"
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
                # Return general client info or list of collections?
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
                # Check if collection has language metadata matching the requested language
                if metadata.get("language") == language:
                    matching_collections.append(collection.name)
                # Fallback: check if collection name contains the language code
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
                # Get language from metadata
                if "language" in metadata:
                    languages.add(metadata["language"])
                # Fallback: extract language from collection name
                elif collection.name.startswith("intent_"):
                    lang = collection.name.split("_", 1)[1]
                    languages.add(lang)
                elif "_" in collection.name:
                    # Assume last part of name is language code
                    parts = collection.name.split("_")
                    if len(parts) > 1:
                        languages.add(parts[-1])

            return list(languages)
        except Exception as e:
            logger.error(f"Error getting available languages: {e}")
            return []

    def test_query(self, query_text: str = "why does time go forward?") -> None:
        """Test method to manually query the collection for debugging"""
        try:
            # Test with English collection
            collection_name = "intent_en"

            # Get query vector - THIS IS THE KEY DIFFERENCE
            # Clean the query text to match how the vectors were indexed
            cleaned_query_text = self.text_processor._clean_text(query_text)
            query_vector = self.text_processor.get_text_vector(cleaned_query_text)

            # Query without filters
            results = self.search(
                collection_name=collection_name,
                query_vector=query_vector,
                top_k=10,
                filters=None,
                language=None,
            )

            # Test direct similarity for debugging
            try:
                pattern_to_test = "why does time go forward"
                # Clean both texts for consistent comparison
                cleaned_query = self.text_processor._clean_text(query_text)
                cleaned_pattern = self.text_processor._clean_text(pattern_to_test)
                direct_similarity = self.text_processor.get_similarity(
                    cleaned_query, cleaned_pattern
                )
                logger.info(
                    f"Direct similarity between '{cleaned_query}' and '{cleaned_pattern}': {direct_similarity}"
                )
            except Exception as e:
                logger.error(f"Error calculating direct similarity: {e}")

            logger.info(f"Found {len(results)} results without filters")

        except Exception as e:
            logger.error(f"Error in test_query: {e}", exc_info=True)

    def index_knowledge_base(
        self,
        collection_name: str,
        knowledge_base_data: Dict[str, Any],
        source_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Index all intents from knowledge base into a specific collection.
        source_metadata can include things like 'language', 'source_file', etc.
        """
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

            # Create vectors for each pattern
            for i, pattern in enumerate(patterns):
                try:
                    # Process text and get vector
                    processed = self.text_processor.preprocess_text(pattern)
                    vector = processed["vector"]

                    # Prepare metadata for the vector, including source information
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
                        "source_language": source_lang,  # Add source language
                        "source_collection": collection_name,  # Add source collection name
                        # Add other intent metadata fields if needed
                        # Using get with None to avoid KeyError, then filtering out None values might be cleaner,
                        # but for now, let's add specific ones.
                        "intent_tags": json.dumps(intent_metadata.get("tags", [])),
                        "intent_priority": intent_metadata.get("priority", 1),
                    }

                    # Create vector entry
                    vector_entry = {
                        "id": f"{collection_name}_{intent_id}_pattern_{i}",  # Make ID more unique across collections
                        "vector": vector,
                        "text": pattern,
                        "metadata": vector_metadata,
                    }

                    vectors.append(vector_entry)

                except Exception as e:
                    print(
                        f"Error processing pattern '{pattern}' for intent '{intent_id}': {e}"
                    )
                    # Depending on requirements, you might want to raise or continue
                    continue

        # Add vectors to the specified store
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
        self, query: str, session_context: Optional[Dict[str, Any]]
    ) -> str:
        """Determine the appropriate collection name for a search query.
        This implementation checks session context for language preference,
        with fallback to English collection.
        """
        # 1. Check session context for language preference
        if session_context:
            session_vars = session_context.get("context_variables", {})
            preferred_lang = session_vars.get("preferred_language")
            if preferred_lang:
                # Map language code to the new, clearer collection name convention (e.g., 'en' -> 'intent_en')
                # This mapping should be configurable or follow a known pattern.
                collection_name = f"intent_{preferred_lang}"
                logger.debug(
                    f"Using collection '{collection_name}' based on session context language '{preferred_lang}'"
                )
                return collection_name

        # 2. Attempt language detection on the query (requires a language detection library)
        # For now, we'll use a simple heuristic based on common words in each language
        # In a production environment, you'd want to use a proper language detection library
        if query:
            # Convert query to lowercase for comparison
            query_lower = query.lower()

            # Simple heuristic for Malay language detection
            # Common Malay words/affixes
            ms_indicators = [
                "ada",
                "saya",
                "anda",
                "kami",
                "dia",
                "mereka",
                "akan",
                "sudah",
                "belum",
                "boleh",
                "tidak",
                "apa",
                "bagaimana",
                "mengapa",
                "kenapa",
                "siapa",
                "bila",
                "macam",
                "mana",
                "sini",
                "situ",
                "sana",
                "ini",
                "itu",
                "dengan",
                "untuk",
                "daripada",
                "kepada",
                "dalam",
                "atas",
                "bawah",
                "sebelum",
                "selepas",
                "antara",
                "melalui",
                "sekitar",
                "sepanjang",
                "seluruh",
                "sebahagian",
            ]

            # Count Malay indicators in the query
            ms_count = sum(
                1
                for word in ms_indicators
                if f" {word} " in f" {query_lower} "
                or query_lower.startswith(f"{word} ")
                or query_lower.endswith(f" {word}")
                or query_lower == word
            )

            # If we find enough Malay indicators, assume it's Malay
            if ms_count >= 1:  # Lowered threshold for Malay detection
                logger.debug(
                    f"Detected Malay language based on heuristic. Using 'intent_ms' collection."
                )
                return "intent_ms"

            # For English, we can use a similar approach or just default to English
            # Common English words/affixes
            en_indicators = [
                "the",
                "is",
                "are",
                "was",
                "were",
                "have",
                "has",
                "had",
                "do",
                "does",
                "did",
                "will",
                "would",
                "could",
                "should",
                "may",
                "might",
                "can",
                "what",
                "where",
                "when",
                "why",
                "how",
                "who",
                "whom",
                "whose",
                "which",
                "this",
                "that",
                "these",
                "those",
                "here",
                "there",
                "i",
                "you",
                "he",
                "she",
                "it",
                "we",
                "they",
                "me",
                "him",
                "her",
                "us",
                "them",
                "my",
                "your",
                "his",
                "her",
                "its",
                "our",
                "their",
                "mine",
                "yours",
                "hers",
                "ours",
                "theirs",
            ]

            # Count English indicators in the query
            en_count = sum(
                1
                for word in en_indicators
                if f" {word} " in f" {query_lower} "
                or query_lower.startswith(f"{word} ")
                or query_lower.endswith(f" {word}")
                or query_lower == word
            )

            # If we find enough English indicators, assume it's English
            if en_count >= 1:  # Lowered threshold for English detection
                logger.debug(
                    f"Detected English language based on heuristic. Using 'intent_en' collection."
                )
                return "intent_en"

        # 3. Default fallback collection
        # This should probably be configurable. For now, let's assume a default like 'en' or a generic one if it exists.
        # Or raise an error if no clear default can be determined and language is crucial.
        logger.info(
            "Could not determine specific language for search. Using default 'intent_en'."
        )
        return "intent_en"  # Or raise ConfigurationError if strict language separation is required.

    def search_intents(
        self,
        query: str,
        session_context: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        collection_name: Optional[str] = None,  # Allow explicit collection name
    ) -> List[Dict[str, Any]]:
        """Search for matching intents with session context, determining the correct collection."""
        try:
            # Determine the collection to search based on query/session or use explicit collection
            if collection_name:
                logger.debug(
                    f"Using explicit collection '{collection_name}' for query: {query[:50]}..."
                )
            else:
                collection_name = self._determine_collection_for_search(
                    query, session_context
                )
                logger.debug(
                    f"Searching collection '{collection_name}' for query: {query[:50]}..."
                )

            # For intent matching, use the original query directly without context enhancement
            # Context enhancement can change the query meaning and hurt matching accuracy
            enhanced_query = query

            # Clean the query text to match how the vectors were indexed
            cleaned_query = self.text_processor._clean_text(enhanced_query)

            # Get query vector from the cleaned text
            query_vector = self.text_processor.get_text_vector(cleaned_query)

            # Build filters based on session context (potentially add language filter here too if not determined by collection)
            filters = self._build_context_filters(session_context)

            # Example: Enforce language filter based on collection if needed (though collection separation often handles this)
            # if collection_name.endswith("_en"):
            #     filters = filters or {}
            #     filters["source_language"] = "en"

            # Search vector store in the determined collection
            # Note: Filters were temporarily disabled in the original. Re-enabling them now.
            results = self.search(
                collection_name=collection_name,
                query_vector=query_vector,
                top_k=top_k,
                filters=filters,
                language=None,  # Language is already handled by collection separation
            )

            # Filter by confidence threshold and add context scoring
            filtered_results = []
            for result in results:
                score = result.get("score", 0)
                metadata = result.get("metadata", {})
                # Use a default threshold if not specified in metadata
                threshold = metadata.get(
                    "confidence_threshold", self.confidence_threshold
                )

                # Add context-aware scoring
                context_score = self._calculate_context_score(result, session_context)
                final_score = (score * 0.7) + (context_score * 0.3)
                result["final_score"] = final_score
                result["context_score"] = context_score
                result["original_score"] = score
                result["threshold"] = threshold

                filtered_results.append(result)

            # Sort by final score
            filtered_results.sort(key=lambda x: x["final_score"], reverse=True)

            # Apply threshold filtering after sorting and scoring
            threshold_filtered_results = []
            for r in filtered_results:
                final_score = r.get("final_score", 0)
                threshold = r.get("threshold", self.confidence_threshold)
                if final_score >= threshold:
                    threshold_filtered_results.append(r)

            return threshold_filtered_results

        except Exception as e:
            logging.error(f"Error in search_intents: {e}", exc_info=True)
            # Consider re-raising configuration errors
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

        # Filter by conversation state
        last_intent = context.get("context_variables", {}).get("last_intent")
        if last_intent:
            # Could implement intent-flow logic here
            pass

        # Example: Add a filter based on a context variable if it exists
        # user_id = context.get("context_variables", {}).get("user_id")
        # if user_id:
        #     filters["user_id"] = user_id

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

    # Get stats for specific known or all collections if needed
        # For now, just return the client info and processor info
        collection_specific_stats = {}
        # Example of getting stats for a couple of collections if you know their names:
        #     try:
        #         collection_specific_stats[f"alfred_knowledge_{lang}"] = self.get_stats(f"alfred_knowledge_{lang}")
        #     except Exception as e:
        #         collection_specific_stats[f"alfred_knowledge_{lang}"] = {"status": f"error: {e}"}

        return {
            "vector_store_client": client_stats,
            "text_processor": processor_stats,
            "service_config": {
                "confidence_threshold": self.confidence_threshold,
                "store_type": client_stats.get("store_type", "unknown"),
                # "default_collection": self.collection_name, # Removed
            },
            # "collections": collection_specific_stats, # Optional detailed stats per collection
        }


# Create a global singleton instance (MUST be AFTER the class definition)
vector_search_service = VectorSearchService()
