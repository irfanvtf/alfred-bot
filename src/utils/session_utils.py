from typing import Optional, Dict, Any
from src.models.session import ConversationMessage, MessageRole
from src.services.session_manager import session_manager


def create_user_message(
    message: str, metadata: Optional[Dict[str, Any]] = None
) -> ConversationMessage:
    """Create a user message object"""
    return ConversationMessage(
        role=MessageRole.USER, message=message, metadata=metadata or {}
    )


def create_bot_message(
    message: str, metadata: Optional[Dict[str, Any]] = None
) -> ConversationMessage:
    """Create a bot message object"""
    return ConversationMessage(
        role=MessageRole.BOT, message=message, metadata=metadata or {}
    )


def extract_entities_from_context(session_id: str) -> Dict[str, Any]:
    """Extract important entities from conversation context"""
    session = session_manager.get_session(session_id)

    if not session:
        return {}

    entities = {}

    # Extract from context variables
    entities.update(session.context_variables)

    # Extract from recent conversation (simple keyword extraction)
    recent_context = session_manager.get_conversation_context(session_id, 3)

    # TODO: Add simple entity extraction logic here
    # This is a placeholder - you can enhance with spaCy NER later

    return entities


def get_session_summary(session_id: str) -> Dict[str, Any]:
    """Get a summary of the session"""
    session = session_manager.get_session(session_id)

    if not session:
        return {}

    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "message_count": len(session.conversation_history),
        "create_at": session.created_at.isoformat(),
        "last_active": session.last_active.isoformat(),
        "is_active": session.is_active,
        "context_keys": list(session.context_variables.keys()),
    }
