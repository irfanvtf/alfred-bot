# src/services/chatbot_engine.py
import random
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from src.services.vector_search import VectorSearchService
from src.services.session_manager import session_manager
# Import the refactored KnowledgeManager
from src.services.knowledge_manager import KnowledgeManager
from src.models.session import SessionUpdate
from src.models.intent import ChatResponse
from src.models.conversation_state import ConversationState
from src.utils.session_utils import create_user_message, create_bot_message
from src.models.session import SessionCreate

logger = logging.getLogger(__name__)


class ChatbotEngine:
    """Main chatbot engine with session-aware logic"""

    def __init__(self, language: str = "en"):
        self.vector_service = VectorSearchService()
        self.language = language
        
        # Use a single KnowledgeManager instance for all sources
        self.knowledge_manager = KnowledgeManager()
        # Register main and fallback knowledge sources for the specified language
        if language == "ms":
            self.knowledge_manager.register_knowledge_source("main", "data/sources/ms/dialog-ms.json")
            self.knowledge_manager.register_knowledge_source("fallback", "data/fallback/ms/fallback-responses.json")
        else:  # default to English
            self.knowledge_manager.register_knowledge_source("main", "data/sources/en/dialog-en.json")
            self.knowledge_manager.register_knowledge_source("fallback", "data/fallback/en/fallback-responses.json")
        
        # Set appropriate confidence thresholds
        self.confidence_threshold = 0.6  # Standard threshold for high confidence matches
        self.fallback_threshold = 0.3   # Lower threshold for fallback responses

        self._initialize_services()
        logger.info(f"ChatbotEngine initialized for language: {language}")

    def _initialize_services(self):
        """Initialize vector service client. Indexing is handled separately."""
        try:
            # Ensure the main knowledge base for this language is loaded using the identifier "main"
            self.knowledge_manager.load_knowledge_base("main")
            
            # Ensure the fallback knowledge base is loaded using the identifier "fallback"
            self.knowledge_manager.load_knowledge_base("fallback")

            # Initialize the vector service client
            self.vector_service.initialize()
            
            # Run a test query for debugging
            if self.language == "en":
                logger.info("Running test query for English engine...")
                self.vector_service.test_query("why does time go forward?")
            
            # Note: Indexing is now handled externally before ChatbotEngine instances are created.
            # This engine will use pre-existing collections named 'intent_{self.language}'.
            
            logger.info(f"Chatbot engine client for language '{self.language}' initialized successfully.")

        except Exception as e:
            logger.error(f"Failed to initialize chatbot engine client for language '{self.language}': {e}")
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
            logger.info(f"Processing message in {self.language} engine: {message[:50]}...")
            logger.debug(f"Original message: '{message}'")
            logger.debug(f"Message length: {len(message)}")
            logger.debug(f"Message repr: {repr(message)}")
            
            # Store original message before lowercasing
            original_message = message
            message = message.lower()
            logger.debug(f"Lowercased message: '{message}'")

            session = self._get_or_create_session(session_id, user_id)
            session_id = session.session_id

            user_message = create_user_message(original_message)  # Use original for session
            session_manager.add_message(session_id, user_message)

            # IMPORTANT: Pass session context to search_intents so it can determine the collection
            # The session context might need to include language information if not determined otherwise.
            # For now, we rely on the engine's self.language or the service's determination logic.
            # If language should be tied to the user/session, it should be part of session_context.
            session_context = session_manager.build_session_context(session_id)
            # Example of potentially adding language to session context if needed by downstream logic
            # session_context.setdefault("context_variables", {})["preferred_language"] = self.language

            intent_matches = self._classify_intent(message, session_context)  # Use lowercased for search
            logger.info(f"Found {len(intent_matches)} intent matches")

            response_data = self._select_response(
                intent_matches, session_context, original_message  # Use original for response
            )

            self._update_conversation_state(session_id, response_data)

            final_response = self._generate_response_text(
                response_data, session_context
            )

            bot_message = create_bot_message(
                final_response,
                metadata={
                    "intent_id": response_data.get("intent_id"),
                    "confidence": response_data.get("confidence", 0.0),
                    "response_type": response_data.get("type", "intent_match"),
                },
            )
            session_manager.add_message(session_id, bot_message)

            chat_response = ChatResponse(
                response=final_response,
                intent_id=response_data.get("intent_id"),
                response_id=response_data.get("response_id"),
                confidence=response_data.get("confidence", 0.0),
                metadata={
                    "session_id": session_id,
                    "conversation_state": session_context.get("conversation_state"),
                    "context_used": bool(session_context.get("conversation_history")),
                    "response_type": response_data.get("type", "intent_match"),
                    "processing_time": datetime.now().isoformat(),
                },
            )

            return chat_response

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

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

        session_create = SessionCreate(
            user_id=user_id,
            initial_context={"conversation_state": ConversationState.GREETING},
        )
        return session_manager.create_session(session_create)

    

    def _classify_intent(
        self, message: str, session_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Classify intent with session context"""
        try:
            # Explicitly specify the collection name based on the engine's language
            collection_name = f"intent_{self.language}"
            
            # Build session context with preferred language to help downstream processing
            enhanced_session_context = session_context.copy() if session_context else {}
            enhanced_session_context.setdefault("context_variables", {})["preferred_language"] = self.language
            
            # The vector_service.search_intents now handles collection determination
            # based on the message and session_context (including potential language info)
            results = self.vector_service.search_intents(
                query=message, 
                session_context=enhanced_session_context, 
                top_k=5,
                collection_name=collection_name  # Explicitly specify collection
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
            
            logger.info(f"Processed {len(intent_matches)} intent matches")
            for match in intent_matches[:3]:
                logger.info(f"Intent match - ID: {match['intent_id']}, Confidence: {match['confidence']:.4f}, Original: {match['original_score']:.4f}, Context: {match['context_score']:.4f}")

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

        logger.info(f"Selecting response from {len(intent_matches)} intent matches")
        
        if not intent_matches:
            logger.info("No intent matches found, using fallback response")
            return self._get_fallback_response(original_message, session_context)

        best_match = intent_matches[0]
        logger.info(f"Best match intent: {best_match.get('intent_id')}, confidence: {best_match.get('confidence')}")
        logger.info(f"Best match details - original_score: {best_match.get('original_score')}, context_score: {best_match.get('context_score')}")

        # Use intent-specific threshold if available, otherwise use engine's default
        # FOR DEBUGGING: Use service threshold instead of intent-specific threshold
        intent_threshold = self.confidence_threshold  # Always use service threshold for debugging
        # ORIGINAL CODE:
        # intent_threshold = best_match.get("metadata", {}).get(
        #     "confidence_threshold", self.confidence_threshold
        # )
        logger.info(f"Intent threshold: {intent_threshold}")

        # Check if confidence meets the required threshold
        if best_match["confidence"] >= intent_threshold:
            logger.info("Confidence meets threshold, using intent response")
            # High confidence - use this intent
            return self._prepare_intent_response(best_match, session_context)

        elif best_match["confidence"] >= self.fallback_threshold:
            logger.info("Confidence meets fallback threshold, checking flow appropriateness")
            # Medium confidence - check conversation flow
            if self._is_flow_appropriate(best_match, session_context):
                logger.info("Flow is appropriate, using intent response")
                return self._prepare_intent_response(best_match, session_context)

        # Low confidence or no matches - use fallback
        logger.info("Low confidence or no appropriate flow, using fallback response")
        return self._get_fallback_response(original_message, session_context)

    def _prepare_intent_response(
        self, intent_match: Dict[str, Any], session_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare response from intent match"""
        try:
            # Handle both old and new formats during transition
            if isinstance(intent_match["responses"], str):
                responses_data = json.loads(intent_match["responses"])
            else:
                responses_data = intent_match["responses"]

            # Convert old format to new format if needed
            if responses_data and isinstance(responses_data[0], str):
                # Old format - convert on the fly
                responses = [
                    {
                        "id": f"{intent_match['intent_id']}_{i}",
                        "text": text,
                    }
                    for i, text in enumerate(responses_data)
                ]
            else:
                # New format
                responses = responses_data

        except Exception as e:
            logger.error(f"Error in _prepare_intent_response: {e}")
            # FIXME: get fallback from JSON
            responses = [
                {
                    "id": "error_0",
                    "text": "I understand, but I'm having trouble with my response.",
                }
            ]

        # Select appropriate response
        selected_response = self._select_appropriate_response(
            responses, session_context, intent_match
        )

        return {
            "type": "intent_match",
            "intent_id": intent_match["intent_id"],
            "confidence": intent_match["confidence"],
            "response": selected_response[
                "text"
            ],  # Keep text for backward compatibility
            "response_id": selected_response["id"],  # Add this new field
            "category": intent_match["category"],
            "original_score": intent_match["original_score"],
            "context_score": intent_match["context_score"],
        }

    def _select_appropriate_response(
        self,
        responses: List[Dict[str, str]],  # Now List of dicts instead of strings
        session_context: Dict[str, Any],
        intent_match: Dict[str, Any],
    ) -> Dict[str, str]:  # Return dict with id, text
        """Select most appropriate response based on context"""

        # For greeting intents, check if this is first interaction
        if intent_match["category"] == "greeting":
            message_count = session_context.get("message_count", 0)
            if message_count <= 1:
                # First greeting - use welcoming responses
                greeting_responses = [
                    r
                    for r in responses
                    if "help" in r["text"].lower() or "assist" in r["text"].lower()
                ]
                if greeting_responses:
                    return random.choice(greeting_responses)
            else:
                # Subsequent greeting - use shorter responses
                short_responses = [r for r in responses if len(r["text"].split()) <= 3]
                if short_responses:
                    return random.choice(short_responses)

        # For other intents, select randomly
        return (
            random.choice(responses)
            if responses
            # FIXME: get fallback from JSON
            else {
                "id": "fallback_0",
                "text": "I understand.",
            }
        )

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
        logger.info(f"Generating fallback response for message: {message[:50]}...")
        
        # Load the fallback knowledge base for this language using the identifier "fallback"
        try:
            # Ensure the fallback knowledge base is loaded
            self.knowledge_manager.load_knowledge_base("fallback") # This will load if not cached or cache is invalid
            # Get the specific intent from the loaded fallback knowledge base
            fallback_intent = self.knowledge_manager.get_intent("fallback", "fallback") # identifier, intent_id
            if fallback_intent and fallback_intent.responses:
                logger.info(f"Found fallback intent with {len(fallback_intent.responses)} responses")
                
                # Select a random response object first
                selected_response = random.choice(fallback_intent.responses)

                # Extract id and text from the response object
                if hasattr(selected_response, "text") and hasattr(selected_response, "id"):
                    response_id = selected_response.id
                    response_text = selected_response.text
                elif isinstance(selected_response, dict):
                    response_id = selected_response.get("id", "unknown")
                    response_text = selected_response.get("text", str(selected_response))
                else:
                    # Fallback for string responses
                    response_id = "legacy_response"
                    response_text = str(selected_response)

                logger.debug(f"Selected fallback response ID: {response_id}, Text: {response_text}")
                return {
                    "type": "fallback",
                    "intent_id": "fallback",
                    "response_id": response_id,
                    "confidence": 0.0,
                    "response": response_text,
                    "category": "fallback",
                }
            else:
                logger.warning("Fallback intent not found or has no responses.")
        except Exception as e:
            logger.error(f"Error loading fallback responses: {e}")

        # Final fallback if KB loading or intent retrieval fails
        logger.warning("Using hardcoded final fallback response.")
        return {
            "type": "fallback",
            "intent_id": "fallback",
            "response_id": "hardcoded_fallback_0",
            "confidence": 0.0,
            "response": "I'm sorry, I didn't understand that. Could you please rephrase?",
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
        vector_stats = self.vector_service.get_service_stats() # Use the new method name
        # Get stats for the main knowledge base using its identifier
        kb_stats = self.knowledge_manager.get_stats("main") # Pass the identifier "main"

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
chatbot_engine = ChatbotEngine("en")


def get_chatbot_engine(language: str = "en") -> "ChatbotEngine":
    """Get a chatbot engine instance for the specified language"""
    return ChatbotEngine(language)