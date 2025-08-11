# src/services/knowledge_manager.py
import json
import os
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from src.models.intent import (
    KnowledgeBase,
    Intent,
)  # , IntentMetadata - Not directly used here anymore
from src.utils.exceptions import ConfigurationError


class KnowledgeManager:
    """Manages multiple knowledge base operations with caching"""

    def __init__(self):
        # Dictionary to hold multiple knowledge bases, keyed by an identifier (e.g., language)
        self.knowledge_bases: Dict[str, KnowledgeBase] = {}
        # Dictionary to hold last modified times for caching, keyed by the same identifier
        self._last_modified_times: Dict[str, Optional[float]] = {}
        # Dictionary to hold file paths for each knowledge base
        self.knowledge_files: Dict[str, str] = {}

    def register_knowledge_source(self, identifier: str, file_path: str) -> None:
        """Register a knowledge source file with an identifier."""
        self.knowledge_files[identifier] = file_path
        # Initialize cache placeholders
        self.knowledge_bases[identifier] = None
        self._last_modified_times[identifier] = None

    def _is_cache_valid(self, identifier: str) -> bool:
        """Check if the cached knowledge base for the given identifier is still valid."""
        if (
            identifier not in self.knowledge_bases
            or self.knowledge_bases[identifier] is None
            or identifier not in self._last_modified_times
            or self._last_modified_times[identifier] is None
        ):
            return False

        file_path = self.knowledge_files.get(identifier)
        if not file_path:
            return False  # No file registered for this identifier

        try:
            current_modified_time = os.path.getmtime(file_path)
            return current_modified_time <= self._last_modified_times[identifier]
        except OSError:
            # File might have been deleted or moved
            return False

    def invalidate_cache(self, identifier: Optional[str] = None) -> None:
        """Invalidate the cache for a specific knowledge base or all."""
        if identifier:
            if identifier in self.knowledge_bases:
                self.knowledge_bases[identifier] = None
            if identifier in self._last_modified_times:
                self._last_modified_times[identifier] = None
        else:
            # Invalidate all caches
            for key in self.knowledge_bases:
                self.knowledge_bases[key] = None
            for key in self._last_modified_times:
                self._last_modified_times[key] = None

    def load_knowledge_base(self, identifier: str) -> KnowledgeBase:
        """Load a knowledge base by identifier from its JSON file with caching."""
        # Return cached version if it's valid
        if self._is_cache_valid(identifier):
            return self.knowledge_bases[identifier]

        file_path = self.knowledge_files.get(identifier)
        if not file_path:
            raise ConfigurationError(
                f"No file registered for knowledge base identifier: {identifier}"
            )
        if not os.path.exists(file_path):
            raise ConfigurationError(f"Knowledge base file not found: {file_path}")

        try:
            # Get file modification time before reading
            current_modified_time = os.path.getmtime(file_path)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Ensure 'metadata' exists and add default fields if missing in the top-level metadata
            if "metadata" not in data:
                data["metadata"] = {}
            metadata = data["metadata"]
            # Add language from metadata if present, otherwise default to identifier or 'unknown'
            language = metadata.get(
                "language", identifier
            )  # Prioritize metadata language, fallback to identifier
            metadata["language"] = language  # Ensure language is set in the loaded data

            # Add default timestamps if not present in intent metadata
            for intent_data in data.get("intents", []):
                if "metadata" not in intent_data:
                    intent_data["metadata"] = {}

                intent_metadata = intent_data["metadata"]
                if "category" not in intent_metadata:
                    intent_metadata["category"] = "general"
                if "created_at" not in intent_metadata:
                    intent_metadata["created_at"] = datetime.now().isoformat()
                if "updated_at" not in intent_metadata:
                    intent_metadata["updated_at"] = datetime.now().isoformat()
                # Ensure language is also propagated to intent metadata if not present
                if "language" not in intent_metadata:
                    intent_metadata["language"] = language

            knowledge_base = KnowledgeBase(**data)
            self.knowledge_bases[identifier] = knowledge_base
            self._last_modified_times[identifier] = current_modified_time
            return knowledge_base

        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in knowledge base '{identifier}' ({file_path}): {e}"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Error loading knowledge base '{identifier}' ({file_path}): {e}"
            )

    # save_knowledge_base is removed as it's not immediately needed for the multi-source loading goal
    # and the logic would need significant changes to handle multiple files/identifiers correctly if saving back is required.
    # If needed, it would require an identifier parameter and save to the registered file path for that identifier.

    # Methods that operated on a single knowledge base need to be updated to take an identifier
    # or work on a default one. For now, we'll make them take an identifier explicitly.

    def _ensure_loaded(self, identifier: str) -> None:
        """Helper to ensure a knowledge base is loaded."""
        if (
            identifier not in self.knowledge_bases
            or self.knowledge_bases[identifier] is None
        ):
            self.load_knowledge_base(identifier)

    def get_intent(self, identifier: str, intent_id: str) -> Optional[Intent]:
        """Get a specific intent by ID from a specified knowledge base."""
        self._ensure_loaded(identifier)
        knowledge_base = self.knowledge_bases[identifier]
        if knowledge_base:
            for intent in knowledge_base.intents:
                if intent.id == intent_id:
                    return intent
        return None

    def get_all_intents(self, identifier: str) -> List[Intent]:
        """Get all intents from a specified knowledge base."""
        self._ensure_loaded(identifier)
        knowledge_base = self.knowledge_bases[identifier]
        return knowledge_base.intents if knowledge_base else []

    def get_intents_by_category(self, identifier: str, category: str) -> List[Intent]:
        """Get intents by category from a specified knowledge base."""
        self._ensure_loaded(identifier)
        knowledge_base = self.knowledge_bases[identifier]
        if knowledge_base:
            return [
                intent
                for intent in knowledge_base.intents
                if intent.metadata.category.lower() == category.lower()
            ]
        return []

    def get_all_registered_identifiers(self) -> List[str]:
        """Get a list of all registered knowledge base identifiers."""
        return list(self.knowledge_files.keys())

    def get_knowledge_base_data(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Get the raw data dictionary of a loaded knowledge base."""
        self._ensure_loaded(identifier)
        knowledge_base = self.knowledge_bases[identifier]
        if knowledge_base:
            # Use model_dump to get a dictionary representation
            return knowledge_base.model_dump()
        return None

    def get_cache_status(
        self, identifier: Optional[str] = None
    ) -> Union[Dict[str, Any], Dict[str, Dict[str, Any]]]:
        """Get cache status information for a specific knowledge base or all."""
        if identifier:
            file_path = self.knowledge_files.get(identifier, "")
            file_exists = os.path.exists(file_path) if file_path else False
            current_file_time = None

            if file_exists:
                try:
                    current_file_time = os.path.getmtime(file_path)
                except OSError:
                    current_file_time = None

            return {
                "identifier": identifier,
                "is_cached": self.knowledge_bases.get(identifier) is not None,
                "cache_valid": self._is_cache_valid(identifier),
                "file_exists": file_exists,
                "file_path": file_path,
                "cached_file_time": self._last_modified_times.get(identifier),
                "current_file_time": current_file_time,
                "cache_outdated": (
                    current_file_time is not None
                    and self._last_modified_times.get(identifier) is not None
                    and current_file_time > self._last_modified_times.get(identifier)
                ),
            }
        else:
            # Return status for all registered knowledge bases
            status = {}
            for ident in self.get_all_registered_identifiers():
                status[ident] = self.get_cache_status(
                    ident
                )  # Recursive call for single identifier
            return status

    def get_stats(self, identifier: str) -> Dict[str, Any]:
        """Get knowledge base statistics for a specific knowledge base."""
        self._ensure_loaded(identifier)
        knowledge_base = self.knowledge_bases[identifier]
        if not knowledge_base:
            return {"error": f"Knowledge base '{identifier}' not loaded."}

        total_intents = len(knowledge_base.intents)
        total_patterns = sum(len(intent.patterns) for intent in knowledge_base.intents)
        total_responses = sum(
            len(intent.responses) for intent in knowledge_base.intents
        )

        categories = {}
        for intent in knowledge_base.intents:
            category = intent.metadata.category
            categories[category] = categories.get(category, 0) + 1

        return {
            "identifier": identifier,
            "total_intents": total_intents,
            "total_patterns": total_patterns,
            "total_responses": total_responses,
            "categories": categories,
            "version": knowledge_base.version,
            "language": getattr(
                knowledge_base.metadata, "language", "unknown"
            ),  # Get language from KB metadata
            "cache_status": self.get_cache_status(
                identifier
            ),  # Get specific cache status
        }


# Global instance (optional, can be instantiated where needed)
# knowledge_manager = KnowledgeManager()
