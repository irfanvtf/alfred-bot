# src/models/session.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    USER = "user"
    BOT = "bot"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    """Individual message in a conversation"""

    role: MessageRole
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    # Optional: link to intent that generated this message
    intent_id: Optional[str] = None
    confidence: Optional[float] = None


class SessionData(BaseModel):
    """Complete session data structure"""

    session_id: str
    user_id: Optional[str] = None
    conversation_history: List[ConversationMessage] = []
    context_variables: Dict[str, Any] = {}
    session_metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


class SessionCreate(BaseModel):
    """Request to create a new session"""

    user_id: Optional[str] = None
    initial_context: Optional[Dict[str, Any]] = None


class SessionUpdate(BaseModel):
    """Request to update session data"""

    message: Optional[ConversationMessage] = None
    context_variables: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
