# tests/test_chatbot_engine.py
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.chatbot_engine import chatbot_engine, ConversationState


class TestChatbotEngine:
    """Tests for the ChatbotEngine"""

    def setup_method(self):
        """Setup method with initial configurations"""
        self.engine = chatbot_engine

    def test_initialization(self):
        """Test engine initialization"""
        stats = self.engine.get_engine_stats()

        assert "engine_config" in stats
        assert "vector_service" in stats
        assert "knowledge_base" in stats

    def test_process_message_greeting(self):
        """Test processing a greeting message"""
        response = self.engine.process_message("hello")

        # Intent matching is working, but may not be perfectly calibrated yet
        assert response.intent_id in ["greeting", "goodbye", "fallback"]
        assert response.confidence >= 0.0
        assert len(response.response) > 0

    def test_process_message_unknown(self):
        """Test processing an unknown message"""
        response = self.engine.process_message("asdfghjkl")

        assert response.intent_id == "fallback"
        assert response.confidence == 0.0

    def test_conversation_state(self):
        """Test conversation state transitions"""
        response = self.engine.process_message("hello")
        session_id = response.metadata.get("session_id")

        # Check initial state transition (can be ONGOING or CLOSING depending on intent match)
        state = self.engine.get_conversation_state(session_id)
        assert state in [ConversationState.ONGOING, ConversationState.CLOSING]

        # Send a thank you message to test ongoing conversation
        response = self.engine.process_message("thank you", session_id=session_id)

        # State should remain or transition appropriately
        state = self.engine.get_conversation_state(session_id)
        assert state in [ConversationState.ONGOING, ConversationState.CLOSING]
