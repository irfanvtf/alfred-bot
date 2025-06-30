# test_knowledge_manager.py
import pytest
import json
import os
import tempfile
from datetime import datetime
from unittest.mock import patch, mock_open
from src.services.knowledge_manager import KnowledgeManager
from src.models.intent import KnowledgeBase, Intent, IntentMetadata
from src.utils.exceptions import ConfigurationError


# Simple test as requested
def simple_test():
    """Simple test to load knowledge base and print stats"""
    km = KnowledgeManager()
    kb = km.load_knowledge_base()
    print(f"Loaded {len(kb.intents)} intents")
    print(km.get_stats())


class TestKnowledgeManager:
    """Comprehensive test suite for KnowledgeManager"""

    def setup_method(self):
        """Setup test fixtures"""
        self.test_data = {
            "version": "1.0.0",
            "intents": [
                {
                    "id": "greeting",
                    "patterns": ["hello", "hi", "hey"],
                    "responses": ["Hello!", "Hi there!", "Hey!"],
                    "metadata": {
                        "category": "greetings",
                        "priority": 1,
                        "created_at": "2024-01-01T10:00:00",
                        "updated_at": "2024-01-01T10:00:00",
                    },
                },
                {
                    "id": "goodbye",
                    "patterns": ["bye", "goodbye", "see you"],
                    "responses": ["Goodbye!", "See you later!", "Bye!"],
                    "metadata": {
                        "category": "greetings",
                        "priority": 1,
                        "created_at": "2024-01-01T11:00:00",
                        "updated_at": "2024-01-01T11:00:00",
                    },
                },
                {
                    "id": "help",
                    "patterns": ["help", "assist", "support"],
                    "responses": ["How can I help you?", "I'm here to assist!"],
                    "metadata": {
                        "category": "support",
                        "priority": 2,
                        "created_at": "2024-01-01T12:00:00",
                        "updated_at": "2024-01-01T12:00:00",
                    },
                },
            ],
        }

    def test_init(self):
        """Test KnowledgeManager initialization"""
        km = KnowledgeManager()
        assert km.knowledge_file == "data/knowledge_base.json"
        assert km.knowledge_base is None

        custom_km = KnowledgeManager("custom/path.json")
        assert custom_km.knowledge_file == "custom/path.json"

    def test_load_knowledge_base_success(self):
        """Test successful loading of knowledge base"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            kb = km.load_knowledge_base()

            assert isinstance(kb, KnowledgeBase)
            assert kb.version == "1.0.0"
            assert len(kb.intents) == 3
            assert kb.intents[0].id == "greeting"
            assert len(kb.intents[0].patterns) == 3
            assert len(kb.intents[0].responses) == 3

        finally:
            os.unlink(temp_file)

    def test_load_knowledge_base_file_not_found(self):
        """Test loading when file doesn't exist"""
        km = KnowledgeManager("nonexistent.json")

        with pytest.raises(ConfigurationError, match="Knowledge base file not found"):
            km.load_knowledge_base()

    def test_load_knowledge_base_invalid_json(self):
        """Test loading with invalid JSON"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)

            with pytest.raises(
                ConfigurationError, match="Invalid JSON in knowledge base"
            ):
                km.load_knowledge_base()

        finally:
            os.unlink(temp_file)

    def test_load_knowledge_base_adds_timestamps(self):
        """Test that missing timestamps are added during load"""
        data_without_timestamps = {
            "version": "1.0.0",
            "intents": [
                {"id": "test", "patterns": ["test"], "responses": ["Test response"]}
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data_without_timestamps, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            kb = km.load_knowledge_base()

            assert hasattr(kb.intents[0].metadata, "created_at")
            assert hasattr(kb.intents[0].metadata, "updated_at")
            assert kb.intents[0].metadata.created_at is not None
            assert kb.intents[0].metadata.updated_at is not None

        finally:
            os.unlink(temp_file)

    def test_save_knowledge_base(self):
        """Test saving knowledge base"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            kb = KnowledgeBase(**self.test_data)

            km.save_knowledge_base(kb)

            # Verify file was created and contains correct data
            assert os.path.exists(temp_file)

            with open(temp_file, "r") as f:
                saved_data = json.load(f)

            assert saved_data["version"] == "1.0.0"
            assert len(saved_data["intents"]) == 3

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_add_intent(self):
        """Test adding a new intent"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            km.load_knowledge_base()

            new_intent = Intent(
                id="new_intent",
                patterns=["new pattern"],
                responses=["New response"],
                metadata=IntentMetadata(category="test", priority=1),
            )

            km.add_intent(new_intent)

            # Verify intent was added
            assert len(km.knowledge_base.intents) == 4
            added_intent = km.get_intent("new_intent")
            assert added_intent is not None
            assert added_intent.id == "new_intent"

        finally:
            os.unlink(temp_file)

    def test_add_intent_duplicate_id(self):
        """Test adding intent with duplicate ID"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            km.load_knowledge_base()

            duplicate_intent = Intent(
                id="greeting",  # This ID already exists
                patterns=["duplicate"],
                responses=["Duplicate response"],
                metadata=IntentMetadata(category="test", priority=1),
            )

            with pytest.raises(
                ValueError, match="Intent with ID 'greeting' already exists"
            ):
                km.add_intent(duplicate_intent)

        finally:
            os.unlink(temp_file)

    def test_update_intent(self):
        """Test updating an existing intent"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            km.load_knowledge_base()

            updated_intent = Intent(
                id="greeting",
                patterns=["hello", "hi", "hey", "howdy"],  # Added "howdy"
                responses=["Hello!", "Hi there!", "Hey!", "Howdy!"],  # Added response
                metadata=IntentMetadata(category="greetings", priority=1),
            )

            km.update_intent("greeting", updated_intent)

            # Verify intent was updated
            intent = km.get_intent("greeting")
            assert len(intent.patterns) == 4
            assert "howdy" in intent.patterns
            assert len(intent.responses) == 4
            assert "Howdy!" in intent.responses

        finally:
            os.unlink(temp_file)

    def test_update_nonexistent_intent(self):
        """Test updating a non-existent intent"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            km.load_knowledge_base()

            updated_intent = Intent(
                id="nonexistent",
                patterns=["test"],
                responses=["Test"],
                metadata=IntentMetadata(category="test", priority=1),
            )

            with pytest.raises(
                ValueError, match="Intent with ID 'nonexistent' not found"
            ):
                km.update_intent("nonexistent", updated_intent)

        finally:
            os.unlink(temp_file)

    def test_delete_intent(self):
        """Test deleting an intent"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            km.load_knowledge_base()

            assert len(km.knowledge_base.intents) == 3

            km.delete_intent("greeting")

            assert len(km.knowledge_base.intents) == 2
            assert km.get_intent("greeting") is None

        finally:
            os.unlink(temp_file)

    def test_delete_nonexistent_intent(self):
        """Test deleting a non-existent intent"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            km.load_knowledge_base()

            with pytest.raises(
                ValueError, match="Intent with ID 'nonexistent' not found"
            ):
                km.delete_intent("nonexistent")

        finally:
            os.unlink(temp_file)

    def test_get_intent(self):
        """Test getting a specific intent"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            km.load_knowledge_base()

            intent = km.get_intent("greeting")
            assert intent is not None
            assert intent.id == "greeting"
            assert len(intent.patterns) == 3

            nonexistent = km.get_intent("nonexistent")
            assert nonexistent is None

        finally:
            os.unlink(temp_file)

    def test_get_all_intents(self):
        """Test getting all intents"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            km.load_knowledge_base()

            all_intents = km.get_all_intents()
            assert len(all_intents) == 3
            assert all([isinstance(intent, Intent) for intent in all_intents])

        finally:
            os.unlink(temp_file)

    def test_get_intents_by_category(self):
        """Test getting intents by category"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            km.load_knowledge_base()

            greeting_intents = km.get_intents_by_category("greetings")
            assert len(greeting_intents) == 2
            assert all(
                intent.metadata.category == "greetings" for intent in greeting_intents
            )

            support_intents = km.get_intents_by_category("support")
            assert len(support_intents) == 1
            assert support_intents[0].id == "help"

            # Test case insensitive search
            greeting_intents_upper = km.get_intents_by_category("GREETINGS")
            assert len(greeting_intents_upper) == 2

        finally:
            os.unlink(temp_file)

    def test_get_stats(self):
        """Test getting knowledge base statistics"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            km = KnowledgeManager(temp_file)
            km.load_knowledge_base()

            stats = km.get_stats()

            assert stats["total_intents"] == 3
            assert stats["total_patterns"] == 9  # 3 + 3 + 2
            assert stats["total_responses"] == 8  # 3 + 3 + 2
            assert stats["version"] == "1.0.0"
            assert stats["categories"]["greetings"] == 2
            assert stats["categories"]["support"] == 1

        finally:
            os.unlink(temp_file)

    def test_knowledge_base_persistence(self):
        """Test that changes persist across manager instances"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self.test_data, f)
            temp_file = f.name

        try:
            # First manager instance
            km1 = KnowledgeManager(temp_file)
            km1.load_knowledge_base()

            new_intent = Intent(
                id="persistence_test",
                patterns=["test persistence"],
                responses=["Persistence works!"],
                metadata=IntentMetadata(category="test", priority=1),
            )
            km1.add_intent(new_intent)

            # Second manager instance
            km2 = KnowledgeManager(temp_file)
            km2.load_knowledge_base()

            # Verify the new intent persists
            persistent_intent = km2.get_intent("persistence_test")
            assert persistent_intent is not None
            assert persistent_intent.patterns == ["test persistence"]

        finally:
            os.unlink(temp_file)


if __name__ == "__main__":
    # Run the simple test
    print("Running simple test:")
    try:
        simple_test()
    except Exception as e:
        print(f"Simple test failed: {e}")

    # Run pytest for comprehensive tests
    print("\nRunning comprehensive tests:")
    pytest.main([__file__, "-v"])
