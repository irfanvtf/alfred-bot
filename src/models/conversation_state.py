# src/models/conversation_state.py
from enum import Enum


class ConversationState(str, Enum):
    """Conversation states for flow management"""

    GREETING = "greeting"
    ONGOING = "ongoing"
    CLOSING = "closing"
    ENDED = "ended"