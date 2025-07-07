# tests/test_intent_models.py
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.intent import ChatRequest, ChatResponse, Intent, IntentMetadata, KnowledgeBase
from pydantic import ValidationError


class TestChatRequest:
    """Test suite for ChatRequest validation"""

    def test_valid_message(self):
        """Test that valid messages are accepted"""
        valid_messages = [
            "Hello world",
            "How are you?",
            "What's the weather like?",
            "a",  # Single character
            "Hello! What's up? 🤖",  # Special characters and emojis
        ]
        
        for message in valid_messages:
            request = ChatRequest(message=message)
            assert request.message == message

    def test_message_trimming(self):
        """Test that messages with leading/trailing whitespace are trimmed"""
        test_cases = [
            ("  hello world  ", "hello world"),
            ("  single  ", "single"),
            ("\t\nhello\t\n", "hello"),
            ("   test message   ", "test message"),
        ]
        
        for input_msg, expected_output in test_cases:
            request = ChatRequest(message=input_msg)
            assert request.message == expected_output

    def test_empty_message_rejected(self):
        """Test that empty messages are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="")
        
        # Check that the error is about string length
        error = exc_info.value.errors()[0]
        assert error["type"] == "string_too_short"
        assert error["ctx"]["min_length"] == 1

    def test_whitespace_only_message_rejected(self):
        """Test that whitespace-only messages are rejected"""
        whitespace_messages = [
            "   ",  # Spaces only
            "\t\t",  # Tabs only
            "\n\n",  # Newlines only
            "\r\r",  # Carriage returns only
            "  \t\n\r  ",  # Mixed whitespace
        ]
        
        for message in whitespace_messages:
            with pytest.raises(ValidationError) as exc_info:
                ChatRequest(message=message)
            
            # Check that the error is from our custom validator
            error = exc_info.value.errors()[0]
            assert error["type"] == "value_error"
            assert "empty or contain only whitespace" in error["msg"]

    def test_optional_fields(self):
        """Test that optional fields work correctly"""
        # Test with minimal required fields
        request = ChatRequest(message="hello")
        assert request.message == "hello"
        assert request.session_id is None
        assert request.user_id is None
        assert request.context == {}

        # Test with all fields
        request = ChatRequest(
            message="hello",
            session_id="session_123",
            user_id="user_456",
            context={"key": "value"}
        )
        assert request.message == "hello"
        assert request.session_id == "session_123"
        assert request.user_id == "user_456"
        assert request.context == {"key": "value"}


class TestChatResponse:
    """Test suite for ChatResponse validation"""

    def test_valid_response(self):
        """Test that valid responses are created correctly"""
        response = ChatResponse(
            response="Hello there!",
            confidence=0.8,
            intent_id="greeting",
            metadata={"test": "value"}
        )
        
        assert response.response == "Hello there!"
        assert response.confidence == 0.8
        assert response.intent_id == "greeting"
        assert response.metadata == {"test": "value"}

    def test_confidence_validation(self):
        """Test that confidence score validation works"""
        # Valid confidence scores
        valid_scores = [0.0, 0.5, 1.0, 0.25, 0.99]
        for score in valid_scores:
            response = ChatResponse(response="test", confidence=score)
            assert response.confidence == score

        # Invalid confidence scores
        invalid_scores = [-0.1, 1.1, -1.0, 2.0]
        for score in invalid_scores:
            with pytest.raises(ValidationError):
                ChatResponse(response="test", confidence=score)

    def test_optional_fields(self):
        """Test optional fields in ChatResponse"""
        # Minimal response
        response = ChatResponse(response="test", confidence=0.5)
        assert response.response == "test"
        assert response.confidence == 0.5
        assert response.intent_id is None
        assert response.metadata == {}


class TestIntent:
    """Test suite for Intent validation"""

    def test_valid_intent(self):
        """Test that valid intents are created correctly"""
        metadata = IntentMetadata(category="test")
        intent = Intent(
            id="test_intent",
            patterns=["hello", "hi"],
            responses=["Hello!", "Hi there!"],
            metadata=metadata
        )
        
        assert intent.id == "test_intent"
        assert intent.patterns == ["hello", "hi"]
        assert intent.responses == ["Hello!", "Hi there!"]

    def test_id_normalization(self):
        """Test that intent IDs are normalized correctly"""
        metadata = IntentMetadata(category="test")
        
        test_cases = [
            ("Test Intent", "test_intent"),
            ("  HELLO  ", "hello"),
            ("Multiple   Spaces", "multiple_spaces"),
            ("MixedCase", "mixedcase"),
        ]
        
        for input_id, expected_id in test_cases:
            intent = Intent(
                id=input_id,
                patterns=["test"],
                responses=["test"],
                metadata=metadata
            )
            assert intent.id == expected_id

    def test_empty_id_rejected(self):
        """Test that empty IDs are rejected"""
        metadata = IntentMetadata(category="test")
        
        with pytest.raises(ValidationError):
            Intent(
                id="   ",  # Whitespace only
                patterns=["test"],
                responses=["test"],
                metadata=metadata
            )

    def test_pattern_validation(self):
        """Test that pattern validation works correctly"""
        metadata = IntentMetadata(category="test")
        
        # Valid patterns should work
        intent = Intent(
            id="test",
            patterns=["hello", "  hi  ", "hey"],  # With whitespace
            responses=["Hello!"],
            metadata=metadata
        )
        assert intent.patterns == ["hello", "hi", "hey"]  # Trimmed

        # Empty patterns should be rejected
        with pytest.raises(ValidationError):
            Intent(
                id="test",
                patterns=[""],  # Empty pattern
                responses=["Hello!"],
                metadata=metadata
            )

        with pytest.raises(ValidationError):
            Intent(
                id="test",
                patterns=["  ", "\t"],  # Whitespace-only patterns
                responses=["Hello!"],
                metadata=metadata
            )

    def test_response_validation(self):
        """Test that response validation works correctly"""
        metadata = IntentMetadata(category="test")
        
        # Valid responses should work
        intent = Intent(
            id="test",
            patterns=["hello"],
            responses=["Hello!", "  Hi there!  "],  # With whitespace
            metadata=metadata
        )
        assert intent.responses == ["Hello!", "Hi there!"]  # Trimmed

        # Empty responses should be rejected
        with pytest.raises(ValidationError):
            Intent(
                id="test",
                patterns=["hello"],
                responses=[""],  # Empty response
                metadata=metadata
            )


class TestIntentMetadata:
    """Test suite for IntentMetadata validation"""

    def test_valid_metadata(self):
        """Test that valid metadata is created correctly"""
        metadata = IntentMetadata(
            category="greeting",
            confidence_threshold=0.8,
            priority=2,
            tags=["hello", "greeting"]
        )
        
        assert metadata.category == "greeting"
        assert metadata.confidence_threshold == 0.8
        assert metadata.priority == 2
        assert metadata.tags == ["hello", "greeting"]

    def test_default_values(self):
        """Test that default values are set correctly"""
        metadata = IntentMetadata(category="test")
        
        assert metadata.category == "test"
        assert metadata.confidence_threshold == 0.7  # Default
        assert metadata.priority == 1  # Default
        assert metadata.tags == []  # Default
        assert metadata.created_at is None  # Default
        assert metadata.updated_at is None  # Default

    def test_confidence_threshold_validation(self):
        """Test that confidence threshold validation works"""
        # Valid thresholds
        valid_thresholds = [0.0, 0.5, 1.0, 0.25, 0.99]
        for threshold in valid_thresholds:
            metadata = IntentMetadata(category="test", confidence_threshold=threshold)
            assert metadata.confidence_threshold == threshold

        # Invalid thresholds
        invalid_thresholds = [-0.1, 1.1, -1.0, 2.0]
        for threshold in invalid_thresholds:
            with pytest.raises(ValidationError):
                IntentMetadata(category="test", confidence_threshold=threshold)

    def test_priority_validation(self):
        """Test that priority validation works"""
        # Valid priorities
        valid_priorities = [1, 5, 10]
        for priority in valid_priorities:
            metadata = IntentMetadata(category="test", priority=priority)
            assert metadata.priority == priority

        # Invalid priorities
        invalid_priorities = [0, 11, -1, 15]
        for priority in invalid_priorities:
            with pytest.raises(ValidationError):
                IntentMetadata(category="test", priority=priority)


class TestKnowledgeBase:
    """Test suite for KnowledgeBase validation"""

    def test_valid_knowledge_base(self):
        """Test that valid knowledge bases are created correctly"""
        metadata1 = IntentMetadata(category="greeting")
        metadata2 = IntentMetadata(category="help")
        
        intent1 = Intent(id="greeting", patterns=["hello"], responses=["Hi!"], metadata=metadata1)
        intent2 = Intent(id="help", patterns=["help"], responses=["How can I help?"], metadata=metadata2)
        
        kb = KnowledgeBase(
            intents=[intent1, intent2],
            version="2.0.0",
            metadata={"description": "Test KB"}
        )
        
        assert len(kb.intents) == 2
        assert kb.version == "2.0.0"
        assert kb.metadata == {"description": "Test KB"}

    def test_unique_intent_ids(self):
        """Test that duplicate intent IDs are rejected"""
        metadata = IntentMetadata(category="test")
        
        intent1 = Intent(id="duplicate", patterns=["hello"], responses=["Hi!"], metadata=metadata)
        intent2 = Intent(id="duplicate", patterns=["hey"], responses=["Hey!"], metadata=metadata)
        
        with pytest.raises(ValidationError) as exc_info:
            KnowledgeBase(intents=[intent1, intent2])
        
        error = exc_info.value.errors()[0]
        assert "unique" in error["msg"].lower()

    def test_default_values(self):
        """Test that default values are set correctly"""
        kb = KnowledgeBase(intents=[])
        
        assert kb.intents == []
        assert kb.version == "1.0.0"  # Default
        assert kb.metadata == {}  # Default


if __name__ == "__main__":
    # Run tests manually if pytest is not available
    import inspect
    
    test_classes = [TestChatRequest, TestChatResponse, TestIntent, TestIntentMetadata, TestKnowledgeBase]
    
    for test_class in test_classes:
        print(f"\n=== Running {test_class.__name__} ===")
        instance = test_class()
        
        # Get all test methods
        test_methods = [method for method in dir(instance) if method.startswith('test_')]
        
        for method_name in test_methods:
            try:
                print(f"Running {method_name}...", end=" ")
                getattr(instance, method_name)()
                print("✅ PASS")
            except Exception as e:
                print(f"❌ FAIL: {e}")
    
    print("\n🎉 Manual test run completed!")
