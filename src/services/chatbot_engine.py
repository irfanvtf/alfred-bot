# src/services/chatbot_engine.py
import random
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json
from src.services.vector_store.search_service import VectorSearchService
from src.services.session_manager import session_manager
from src.services.knowledge_manager import KnowledgeManager
from src.models.session import SessionUpdate
from src.models.intent import ChatResponse
from src.utils.session_utils import create_user_message, create_bot_message

logger = logging.getLogger(__name__)


class ConversationState(str, Enum):
    """Conversation states for flow management"""

    GREETING = "greeting"
    ONGOING = "ongoing"
    CLOSING = "closing"
    ENDED = "ended"


class ChatbotEngine:
    """Main chatbot engine with session-aware logic"""

    def __init__(self):
        self.vector_service = VectorSearchService(use_chroma=True)
        self.knowledge_manager = KnowledgeManager("data/knowledge-base.json")
        self.confidence_threshold = 0.25  # Very low for testing
        self.fallback_threshold = 0.1

        # Initialize services
        self._initialize_services()

    def _initialize_services(self):
        """Initialize vector service with knowledge base"""
        try:
            # Load knowledge base
            knowledge_base = self.knowledge_manager.load_knowledge_base()

            # Initialize vector service
            self.vector_service.initialize()

            # Index knowledge base
            kb_data = knowledge_base.model_dump()
            self.vector_service.index_knowledge_base(kb_data)

            logger.info("Chatbot engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize chatbot engine: {e}")
            raise

    def process_message(
        self,
        message: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Process a user message and generate a response
        """
        try:
            # Get or create session
            session = self._get_or_create_session(session_id, user_id)
            session_id = session.session_id

            # Add user message to session
            user_message = create_user_message(message)
            session_manager.add_message(session_id, user_message)

            # Get session context for enhanced processing
            session_context = self._build_session_context(session_id)

            # Classify intent with session context
            intent_matches = self._classify_intent(message, session_context)

            # Select best response with session awareness
            response_data = self._select_response(
                intent_matches, session_context, message
            )

            # Update conversation state
            self._update_conversation_state(session_id, response_data)

            # Generate final response with templating
            final_response = self._generate_response_text(
                response_data, session_context
            )

            # Add bot response to session
            bot_message = create_bot_message(
                final_response,
                metadata={
                    "intent_id": response_data.get("intent_id"),
                    "confidence": response_data.get("confidence", 0.0),
                    "response_type": response_data.get("type", "intent_match"),
                },
            )
            session_manager.add_message(session_id, bot_message)

            # Create response object
            chat_response = ChatResponse(
                response=final_response,
                intent_id=response_data.get("intent_id"),
                confidence=response_data.get("confidence", 0.0),
                metadata={
                    "session_id": session_id,
                    "conversation_state": session_context.get("conversation_state"),
                    "context_used": bool(session_context.get("conversation_history")),
                    "response_type": response_data.get("type", "intent_match"),
                    "processing_time": datetime.now().isoformat(),
                },
            )

            logger.info(
                f"Processed message for session {session_id}: {response_data.get('intent_id', 'fallback')}"
            )

            return chat_response

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

            # Return fallback response
            return ChatResponse(
                response="I'm sorry, I encountered an error. Please try again.",
                intent_id="error",
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _get_or_create_session(self, session_id: Optional[str], user_id: Optional[str]):
        """Get existing session or create new one"""
        if session_id:
            session = session_manager.get_session(session_id)
            if session:
                return session

        # Create new session
        from src.models.session import SessionCreate

        session_create = SessionCreate(
            user_id=user_id,
            initial_context={"conversation_state": ConversationState.GREETING},
        )
        return session_manager.create_session(session_create)

    def _build_session_context(self, session_id: str) -> Dict[str, Any]:
        """Build comprehensive session context"""
        session = session_manager.get_session(session_id)
        if not session:
            return {}

        # Get conversation history
        conversation_history = []
        for msg in session.conversation_history[-5:]:  # Last 5 messages
            if isinstance(msg, dict):
                conversation_history.append(msg)
            else:
                conversation_history.append(
                    {
                        "role": msg.role,
                        "message": msg.message,
                        "timestamp": msg.timestamp.isoformat()
                        if msg.timestamp
                        else None,
                    }
                )

        # Build context
        context = {
            "session_id": session_id,
            "user_id": session.user_id,
            "conversation_history": conversation_history,
            "context_variables": session.context_variables.copy(),
            "conversation_state": session.context_variables.get(
                "conversation_state", ConversationState.GREETING
            ),
            "last_intent": session.context_variables.get("last_intent"),
            "last_category": session.context_variables.get("last_category"),
            "message_count": len(session.conversation_history),
        }

        return context

    def _classify_intent(
        self, message: str, session_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Classify intent with session context"""
        try:
            # Search for intent matches
            results = self.vector_service.search_intents(
                query=message, session_context=session_context, top_k=5
            )

            # Process and rank results
            intent_matches = []
            for result in results:
                intent_match = {
                    "intent_id": result["metadata"]["intent_id"],
                    "confidence": result.get("final_score", result.get("score", 0)),
                    "original_score": result.get("score", 0),
                    "context_score": result.get("context_score", 0),
                    "matched_pattern": result.get("text", ""),
                    "responses": result["metadata"].get("responses", "[]"),
                    "category": result["metadata"].get("category", "general"),
                    "metadata": result["metadata"],
                }
                intent_matches.append(intent_match)

            return intent_matches

        except Exception as e:
            logger.error(f"Error in intent classification: {e}")
            return []

    def _select_response(
        self,
        intent_matches: List[Dict[str, Any]],
        session_context: Dict[str, Any],
        original_message: str,
    ) -> Dict[str, Any]:
        """Select best response with session awareness"""

        # Debug logging
        logger.debug(
            f"DEBUG: _select_response called with {len(intent_matches)} matches"
        )
        if intent_matches:
            best_match = intent_matches[0]
            logger.debug(
                f"DEBUG: Best match - Intent: {best_match['intent_id']}, Confidence: {best_match['confidence']}, Threshold: {self.confidence_threshold}"
            )

        # Check for high-confidence matches
        if intent_matches:
            best_match = intent_matches[0]

            if best_match["confidence"] >= self.confidence_threshold:
                # High confidence - use this intent
                logger.debug(
                    f"DEBUG: Using high confidence match: {best_match['intent_id']}"
                )
                return self._prepare_intent_response(best_match, session_context)

            elif best_match["confidence"] >= self.fallback_threshold:
                # Medium confidence - check conversation flow
                logger.debug(
                    f"DEBUG: Checking flow appropriateness for medium confidence match"
                )
                if self._is_flow_appropriate(best_match, session_context):
                    logger.debug(
                        f"DEBUG: Flow appropriate, using match: {best_match['intent_id']}"
                    )
                    return self._prepare_intent_response(best_match, session_context)
                else:
                    logger.debug(
                        f"DEBUG: Flow not appropriate for match: {best_match['intent_id']}"
                    )

        # Low confidence or no matches - use fallback
        logger.debug(f"DEBUG: Using fallback response")
        return self._get_fallback_response(original_message, session_context)

    def _prepare_intent_response(
        self, intent_match: Dict[str, Any], session_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare response from intent match"""
        try:
            responses = json.loads(intent_match["responses"])
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.warning(f"Failed to parse intent responses: {e}")
            responses = ["I understand, but I'm having trouble with my response."]
        except Exception as e:
            logger.error(f"Error in _prepare_intent_response: {e}")
            responses = ["I understand, but I'm having trouble with my response."]

        # Select appropriate response
        selected_response = self._select_appropriate_response(
            responses, session_context, intent_match
        )

        return {
            "type": "intent_match",
            "intent_id": intent_match["intent_id"],
            "confidence": intent_match["confidence"],
            "response": selected_response,
            "category": intent_match["category"],
            "original_score": intent_match["original_score"],
            "context_score": intent_match["context_score"],
        }

    def _select_appropriate_response(
        self,
        responses: List[str],
        session_context: Dict[str, Any],
        intent_match: Dict[str, Any],
    ) -> str:
        """Select most appropriate response based on context"""

        # For greeting intents, check if this is first interaction
        if intent_match["category"] == "greeting":
            message_count = session_context.get("message_count", 0)
            if message_count <= 1:
                # First greeting - use welcoming responses
                greeting_responses = [
                    r for r in responses if "help" in r.lower() or "assist" in r.lower()
                ]
                if greeting_responses:
                    return random.choice(greeting_responses)
            else:
                # Subsequent greeting - use shorter responses
                short_responses = [r for r in responses if len(r.split()) <= 3]
                if short_responses:
                    return random.choice(short_responses)

        # For other intents, select randomly for now
        # TODO: Implement more sophisticated selection logic
        return random.choice(responses) if responses else "I understand."

    def _is_flow_appropriate(
        self, intent_match: Dict[str, Any], session_context: Dict[str, Any]
    ) -> bool:
        """Check if intent fits conversation flow"""

        current_intent = intent_match["intent_id"]
        conversation_state = session_context.get("conversation_state")

        # Define conversation flow rules
        flow_rules = {
            ConversationState.GREETING: {
                "allowed_intents": ["greeting", "help", "thanks"],
                "preferred_intents": ["greeting", "help"],
            },
            ConversationState.ONGOING: {
                "allowed_intents": ["help", "thanks", "goodbye", "weather", "greeting"],
                "preferred_intents": ["help", "thanks"],
            },
            ConversationState.CLOSING: {
                "allowed_intents": ["goodbye", "thanks"],
                "preferred_intents": ["goodbye"],
            },
        }

        current_rules = flow_rules.get(conversation_state, {})
        allowed_intents = current_rules.get("allowed_intents", [])
        preferred_intents = current_rules.get("preferred_intents", [])

        # Boost confidence for preferred intents
        if current_intent in preferred_intents:
            return True

        # Allow other intents with some penalty
        if current_intent in allowed_intents:
            return intent_match["confidence"] >= (self.fallback_threshold + 0.1)

        # Strict check for other intents
        return intent_match["confidence"] >= self.confidence_threshold

    def _get_fallback_response(
        self, message: str, session_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback response with context awareness"""

        conversation_state = session_context.get(
            "conversation_state", ConversationState.ONGOING
        )
        message_count = session_context.get("message_count", 0)

        # Context-aware fallback responses
        if conversation_state == ConversationState.GREETING and message_count <= 1:
            responses = [
                "Hello! I'm Alfred, your AI assistant. How can I help you today?",
                "Hi there! I'm here to help. What would you like to know?",
                "Welcome! I'm Alfred. What can I assist you with?",
            ]
        elif "thank" in message.lower() or "thanks" in message.lower():
            responses = [
                "You're welcome! Is there anything else I can help you with?",
                "My pleasure! Let me know if you need anything else.",
                "Happy to help! What else can I do for you?",
            ]
        elif "bye" in message.lower() or "goodbye" in message.lower():
            responses = [
                "Goodbye! Have a great day!",
                "Take care! Feel free to come back anytime.",
                "See you later! Have a wonderful day!",
            ]
        else:
            responses = [
                "I'm not sure I understand that completely. Could you rephrase it?",
                "I don't have specific information about that. Can you ask me something else?",
                "That's not something I'm familiar with yet. How else can I help you?",
                "I'm still learning about that topic. Is there something else I can assist with?",
            ]

        return {
            "type": "fallback",
            "intent_id": "fallback",
            "confidence": 0.0,
            "response": random.choice(responses),
            "category": "fallback",
        }

    def _update_conversation_state(
        self, session_id: str, response_data: Dict[str, Any]
    ):
        """Update conversation state based on response"""

        intent_id = response_data.get("intent_id")
        category = response_data.get("category")

        # Determine new state
        new_state = None
        if intent_id == "greeting":
            new_state = ConversationState.ONGOING
        elif intent_id == "goodbye":
            new_state = ConversationState.CLOSING
        elif category == "farewell":
            new_state = ConversationState.CLOSING

        # Update session context
        update_vars = {
            "last_intent": intent_id,
            "last_category": category,
            "last_response_confidence": response_data.get("confidence", 0.0),
        }

        if new_state:
            update_vars["conversation_state"] = new_state

        session_update = SessionUpdate(context_variables=update_vars)
        session_manager.update_session(session_id, session_update)

    def _generate_response_text(
        self, response_data: Dict[str, Any], session_context: Dict[str, Any]
    ) -> str:
        """Generate final response text with templating"""

        response_text = response_data.get(
            "response", "I'm not sure how to respond to that."
        )

        # Simple template variable replacement
        # TODO: Implement more sophisticated templating

        # Replace user name if available
        user_name = session_context.get("context_variables", {}).get("user_name")
        if user_name and "{user_name}" in response_text:
            response_text = response_text.replace("{user_name}", user_name)

        return response_text

    def get_conversation_state(self, session_id: str) -> Optional[ConversationState]:
        """Get current conversation state"""
        session = session_manager.get_session(session_id)
        if session:
            return session.context_variables.get(
                "conversation_state", ConversationState.GREETING
            )
        return None

    def get_engine_stats(self) -> Dict[str, Any]:
        """Get chatbot engine statistics"""
        vector_stats = self.vector_service.get_stats()
        kb_stats = self.knowledge_manager.get_stats()

        return {
            "engine_config": {
                "confidence_threshold": self.confidence_threshold,
                "fallback_threshold": self.fallback_threshold,
            },
            "vector_service": vector_stats,
            "knowledge_base": kb_stats,
            "active_sessions": session_manager.get_active_session_count(),
        }


# Create global instance
chatbot_engine = ChatbotEngine()
