# src/api/route/chat.py
from fastapi import APIRouter, HTTPException, Query
import logging
from src.models.intent import ChatRequest, ChatResponse
from src.services.chatbot_engine import ChatbotEngine
from src.services.session_manager import session_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Cache for chatbot engines by language
_chatbot_engines = {}

def get_chatbot_engine_cached(language: str = "en") -> ChatbotEngine:
    """Get a cached chatbot engine instance for the specified language"""
    global _chatbot_engines
    if language not in _chatbot_engines:
        logger.info(f"Creating new chatbot engine for language: {language}")
        _chatbot_engines[language] = ChatbotEngine(language)
    return _chatbot_engines[language]


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest, language: str = Query("en", description="Language code for the chatbot")):
    """
    Main chat endpoint with embedded session handling

    Args:
        request: Chat request containing message and optional context
        language: Language code for the chatbot (en, ms, etc.)

    Returns:
        ChatResponse with bot response and metadata
    """
    try:
        logger.info(f"Processing chat request: {request.message[:50]}...")

        # Determine the language to use:
        # 1. Use language from request parameter if provided
        # 2. Use language from request body if provided
        # 3. Default to "en"
        selected_language = language or request.language or "en"

        # Get cached chatbot engine for the specified language
        chatbot_engine = get_chatbot_engine_cached(selected_language)

        # If language is specified in the request, add it to the session context
        if request.language and request.session_id:
            # Update session context with preferred language
            session = session_manager.get_session(request.session_id)
            if session:
                session.context_variables["preferred_language"] = request.language

        response = chatbot_engine.process_message(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id,
        )

        logger.info(f"Chat response generated: {response.intent_id or 'fallback'}")
        return response

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to process chat message: {str(e)}"
        ) from e


@router.post("/session/{session_id}", response_model=ChatResponse)
async def chat_with_session(session_id: str, request: ChatRequest, language: str = Query("en", description="Language code for the chatbot")):
    """
    Chat endpoint with explicit session ID

    Args:
        session_id: Explicit session ID to use
        request: Chat request containing message and optional context
        language: Language code for the chatbot (en, ms, etc.)

    Returns:
        ChatResponse with bot response and metadata
    """
    try:
        # Verify session exists
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        logger.info(f"Processing chat request for session {session_id}")

        # Determine the language to use:
        # 1. Use language from request parameter if provided
        # 2. Use language from request body if provided
        # 3. Default to "en"
        selected_language = language or request.language or "en"

        # Get cached chatbot engine for the specified language
        chatbot_engine = get_chatbot_engine_cached(selected_language)

        # If language is specified in the request, add it to the session context
        if request.language:
            # Update session context with preferred language
            session.context_variables["preferred_language"] = request.language

        # Process message with specific session
        response = chatbot_engine.process_message(
            message=request.message, session_id=session_id, user_id=request.user_id
        )

        logger.info(f"Chat response generated for session {session_id}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat with session endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/stats")
async def get_chat_stats():
    """
    Get chatbot engine statistics

    Returns:
        Dict containing engine statistics and performance metrics
    """
    try:
        # Get the default English chatbot engine for stats
        from src.services.chatbot_engine import chatbot_engine
        stats = chatbot_engine.get_engine_stats()
        return {
            "status": "healthy",
            "stats": stats,
            "active_sessions": session_manager.get_active_session_count(),
        }
    except Exception as e:
        logger.error(f"Error getting chat stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get chat statistics: {str(e)}"
        )


@router.get("/session/{session_id}/context")
async def get_session_context(session_id: str):
    """
    Get current session context and conversation state

    Args:
        session_id: Session ID to get context for

    Returns:
        Dict containing session context and conversation state
    """
    try:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Get the default English chatbot engine for conversation state
        from src.services.chatbot_engine import chatbot_engine
        conversation_state = chatbot_engine.get_conversation_state(session_id)

        return {
            "session_id": session_id,
            "conversation_state": conversation_state,
            "context_variables": session.context_variables,
            "message_count": len(session.conversation_history),
            "last_activity": session.last_activity.isoformat()
            if session.last_activity
            else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session context: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get session context: {str(e)}"
        )
