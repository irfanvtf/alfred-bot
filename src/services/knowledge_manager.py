# src/models/knowledge.py
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.models.intent import KnowledgeBase, Intent, IntentMetadata
from src.utils.exceptions import ConfigurationError


class KnowledgeManager:
    """Manages knowledge base operations with caching"""

    def __init__(self, knowledge_file: str = "data/knowledge/knowledge-base.json"):
        self.knowledge_file = knowledge_file
        self.knowledge_base: Optional[KnowledgeBase] = None
        self._last_modified_time: Optional[float] = None

    def _is_cache_valid(self) -> bool:
        """Check if the cached knowledge base is still valid"""
        if self.knowledge_base is None or self._last_modified_time is None:
            return False

        try:
            current_modified_time = os.path.getmtime(self.knowledge_file)
            return current_modified_time <= self._last_modified_time
        except OSError:
            # File might have been deleted or moved
            return False

    def invalidate_cache(self) -> None:
        """Explicitly invalidate the cache by setting cached knowledge base to None"""
        self.knowledge_base = None
        self._last_modified_time = None

    def load_knowledge_base(self) -> KnowledgeBase:
        """Load knowledge base from JSON file with caching"""
        # Return cached version if it's valid
        if self._is_cache_valid():
            return self.knowledge_base

        if not os.path.exists(self.knowledge_file):
            raise ConfigurationError(
                f"Knowledge base file not found: {self.knowledge_file}"
            )

        try:
            # Get file modification time before reading
            current_modified_time = os.path.getmtime(self.knowledge_file)

            with open(self.knowledge_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Add timestamps if not present
            for intent_data in data.get("intents", []):
                if "metadata" not in intent_data:
                    intent_data["metadata"] = {}

                metadata = intent_data["metadata"]
                if "category" not in metadata:
                    metadata["category"] = "general"
                if "created_at" not in metadata:
                    metadata["created_at"] = datetime.now().isoformat()
                if "updated_at" not in metadata:
                    metadata["updated_at"] = datetime.now().isoformat()

            self.knowledge_base = KnowledgeBase(**data)
            self._last_modified_time = current_modified_time
            return self.knowledge_base

        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in knowledge base: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error loading knowledge base: {e}")

    def save_knowledge_base(self, knowledge_base: KnowledgeBase):
        """Save knowledge base to JSON file and update cache"""
        try:
            # Update timestamps
            for intent in knowledge_base.intents:
                intent.metadata.updated_at = datetime.now()

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.knowledge_file), exist_ok=True)

            with open(self.knowledge_file, "w", encoding="utf-8") as f:
                json.dump(
                    knowledge_base.model_dump(),
                    f,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )

            # Update cache with saved knowledge base and new modification time
            self.knowledge_base = knowledge_base
            self._last_modified_time = os.path.getmtime(self.knowledge_file)

        except Exception as e:
            raise ConfigurationError(f"Error saving knowledge base: {e}")

    def add_intent(self, intent: Intent):
        """Add a new intent to the knowledge base"""
        if not self.knowledge_base:
            self.load_knowledge_base()

        # Check for duplicate IDs
        existing_ids = [i.id for i in self.knowledge_base.intents]
        if intent.id in existing_ids:
            raise ValueError(f"Intent with ID '{intent.id}' already exists")

        intent.metadata.created_at = datetime.now()
        intent.metadata.updated_at = datetime.now()

        self.knowledge_base.intents.append(intent)
        self.save_knowledge_base(self.knowledge_base)

    def update_intent(self, intent_id: str, updated_intent: Intent):
        """Update an existing intent"""
        if not self.knowledge_base:
            self.load_knowledge_base()

        for i, intent in enumerate(self.knowledge_base.intents):
            if intent.id == intent_id:
                updated_intent.metadata.updated_at = datetime.now()
                # Preserve creation timestamp
                if intent.metadata.created_at:
                    updated_intent.metadata.created_at = intent.metadata.created_at

                self.knowledge_base.intents[i] = updated_intent
                self.save_knowledge_base(self.knowledge_base)
                return

        raise ValueError(f"Intent with ID '{intent_id}' not found")

    def delete_intent(self, intent_id: str):
        """Delete an intent from the knowledge base"""
        if not self.knowledge_base:
            self.load_knowledge_base()

        original_length = len(self.knowledge_base.intents)
        self.knowledge_base.intents = [
            intent for intent in self.knowledge_base.intents if intent.id != intent_id
        ]

        if len(self.knowledge_base.intents) == original_length:
            raise ValueError(f"Intent with ID '{intent_id}' not found")

        self.save_knowledge_base(self.knowledge_base)

    def get_intent(self, intent_id: str) -> Optional[Intent]:
        """Get a specific intent by ID"""
        if not self.knowledge_base:
            self.load_knowledge_base()

        for intent in self.knowledge_base.intents:
            if intent.id == intent_id:
                return intent
        return None

    def get_all_intents(self) -> List[Intent]:
        """Get all intents"""
        if not self.knowledge_base:
            self.load_knowledge_base()
        return self.knowledge_base.intents

    def get_intents_by_category(self, category: str) -> List[Intent]:
        """Get intents by category"""
        if not self.knowledge_base:
            self.load_knowledge_base()

        return [
            intent
            for intent in self.knowledge_base.intents
            if intent.metadata.category.lower() == category.lower()
        ]

    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status information for debugging and monitoring"""
        file_exists = os.path.exists(self.knowledge_file)
        current_file_time = None

        if file_exists:
            try:
                current_file_time = os.path.getmtime(self.knowledge_file)
            except OSError:
                current_file_time = None

        return {
            "is_cached": self.knowledge_base is not None,
            "cache_valid": self._is_cache_valid(),
            "file_exists": file_exists,
            "cached_file_time": self._last_modified_time,
            "current_file_time": current_file_time,
            "cache_outdated": (
                current_file_time is not None
                and self._last_modified_time is not None
                and current_file_time > self._last_modified_time
            ),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics"""
        if not self.knowledge_base:
            self.load_knowledge_base()

        total_intents = len(self.knowledge_base.intents)
        total_patterns = sum(
            len(intent.patterns) for intent in self.knowledge_base.intents
        )
        total_responses = sum(
            len(intent.responses) for intent in self.knowledge_base.intents
        )

        categories = {}
        for intent in self.knowledge_base.intents:
            category = intent.metadata.category
            categories[category] = categories.get(category, 0) + 1

        return {
            "total_intents": total_intents,
            "total_patterns": total_patterns,
            "total_responses": total_responses,
            "categories": categories,
            "version": self.knowledge_base.version,
            "cache_status": self.get_cache_status(),
        }


# knowledge_manager = KnowledgeManager()
