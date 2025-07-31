import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict
from config.redis_client import redis_client
from config.settings import settings
from src.models.session import (
    SessionData,
    SessionCreate,
    SessionUpdate,
    ConversationMessage,
)
import logging


logger = logging.getLogger(__name__)


class SessionManager:
    def __init__(self):
        # FIXED: Change this line from redis_client.connection to just redis_client
        self.redis = redis_client.connection
        self.session_prefix = "alfred_session:"
        self.ttl = settings.session_ttl
        self.max_history = int(settings.max_conversation_history)

        # Log deduplication tracking
        self._last_logged_saves = defaultdict(float)  # session_id -> timestamp
        self._save_counts = defaultdict(int)  # session_id -> count since last log
        self._log_cooldown = 5.0  # seconds between duplicate logs

    def get_session_key(self, session_id: str) -> str:
        """Generate Redis session key"""
        return f"{self.session_prefix}{session_id}"

    def create_session(self, session_create: SessionCreate) -> SessionData:
        """Create a new session"""
        session_id = str(uuid.uuid4())

        session_data = SessionData(
            session_id=session_id,
            user_id=session_create.user_id,
            context_variables=session_create.initial_context or {},
        )

        # Store in Redis
        key = self.get_session_key(session_id)
        self.redis.setex(key, self.ttl, session_data.model_dump_json())

        logger.info(f"Created new session {session_id}")
        return session_data

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get a session by ID"""
        key = self.get_session_key(session_id)
        session_json = self.redis.get(key)

        if not session_json:
            return None

        try:
            session_data = SessionData.model_validate_json(session_json)

            # Update timestamp
            session_data.last_active = datetime.utcnow()
            self._save_session(session_data)
            return session_data
        except Exception as e:
            logger.error(f"Error fetching session {session_id}: {e}")
            return None

    def update_session(
        self, session_id: str, update: SessionUpdate
    ) -> Optional[SessionData]:
        """Update a session with new data"""
        session = self.get_session(session_id)

        if not session:
            return None

        # Update message history
        if update.message:
            session.conversation_history.append(update.message)

            # Trim long history
            if len(session.conversation_history) > self.max_history:
                session.conversation_history = session.conversation_history[
                    -self.max_history :
                ]

        # Update context variables
        if update.context_variables:
            session.context_variables.update(update.context_variables)

        # Update active status
        if update.is_active is not None:
            session.is_active = update.is_active

        session.last_active = datetime.utcnow()
        self._save_session(session)

        return session

    def _save_session(self, session: SessionData):
        """Save session to Redis with deduplicated logging"""
        key = self.get_session_key(session.session_id)
        self.redis.setex(key, self.ttl, session.model_dump_json())

        # Track save count
        self._save_counts[session.session_id] += 1

        # Check if we should log based on cooldown period
        now = time.time()
        last_logged = self._last_logged_saves[session.session_id]

        if now - last_logged >= self._log_cooldown:
            count = self._save_counts[session.session_id]
            session_id = session.session_id

            if count == 1:
                logger.debug(f"Saved session: {session_id}.")
            else:
                logger.debug(f"Saved session: {session_id}. ({count} times)")

            # Reset tracking for this session
            self._last_logged_saves[session.session_id] = now
            self._save_counts[session.session_id] = 0

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        key = self.get_session_key(session_id)
        result = self.redis.delete(key)

        # Clean up tracking data
        session_id_key = session_id
        if session_id_key in self._last_logged_saves:
            del self._last_logged_saves[session_id_key]
        if session_id_key in self._save_counts:
            del self._save_counts[session_id_key]

        logger.info(f"Deleted session: {session_id[:8]}...")
        return result > 0

    def add_message(
        self, session_id: str, message: ConversationMessage
    ) -> Optional[SessionData]:
        """Add a message to session conversation history"""
        update = SessionUpdate(message=message)
        return self.update_session(session_id, update)

    def get_conversation_context(
        self, session_id: str, last_n_messages: int = 5
    ) -> str:
        """Get recent conversation context as formatted string"""
        session = self.get_session(session_id)

        if not session:
            return ""

        recent_messages = session.conversation_history[-last_n_messages:]
        context_parts = []

        for msg in recent_messages:
            if isinstance(msg, dict):
                msg = ConversationMessage(**msg)  # parse dict into model

            # Always handle the message if it's a ConversationMessage
            if isinstance(msg, ConversationMessage):
                role_prefix = "User" if msg.role == "user" else "Alfred"
                context_parts.append(f"{role_prefix}: {msg.message}")

        return "\n".join(context_parts)

    def extend_session_ttl(self, session_id: str) -> bool:
        """Extend session TTL"""
        key = self.get_session_key(session_id)
        return self.redis.expire(key, self.ttl)

    def get_active_session_count(self):
        """Get count of active sessions"""
        pattern = f"{self.session_prefix}*"
        return len(self.redis.keys(pattern))

    def cleanup_old_tracking_data(self):
        """Clean up old tracking data to prevent memory leaks"""
        now = time.time()
        cutoff_time = now - (self._log_cooldown * 10)  # Keep 10x cooldown period

        # Remove old entries
        old_sessions = [
            session_id
            for session_id, timestamp in self._last_logged_saves.items()
            if timestamp < cutoff_time
        ]

        for session_id in old_sessions:
            del self._last_logged_saves[session_id]
            if session_id in self._save_counts:
                del self._save_counts[session_id]


session_manager = SessionManager()
