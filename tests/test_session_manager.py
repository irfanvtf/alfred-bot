import pytest
import time
from datetime import datetime

from src.services.session_manager import session_manager
from src.models.session import (
    SessionCreate,
    SessionUpdate,
    ConversationMessage,
    MessageRole,
)
from config.redis_client import redis_client
from src.utils.session_utils import create_user_message, create_bot_message


@pytest.fixture(autouse=True)
def clean_test_sessions():
    """Auto-clean all test Redis keys before/after tests"""
    keys = redis_client.connection.keys("alfred_session:*")
    if keys:
        redis_client.connection.delete(*keys)
    yield
    keys = redis_client.connection.keys("alfred_session:*")
    if keys:
        redis_client.connection.delete(*keys)


def test_create_and_retrieve_session():
    """Create and retrieve session"""
    session_create = SessionCreate(
        user_id="user123", initial_context={"topic": "order"}
    )
    session = session_manager.create_session(session_create)

    assert session.session_id is not None
    assert session.user_id == "user123"
    assert session.context_variables["topic"] == "order"
    assert session.is_active is True

    retrieved = session_manager.get_session(session.session_id)
    assert retrieved is not None
    assert retrieved.session_id == session.session_id
    assert retrieved.context_variables["topic"] == "order"


def test_add_messages_and_truncate_history():
    """Test adding multiple messages and automatic truncation"""
    session = session_manager.create_session(SessionCreate())

    max_history = session_manager.max_history
    for i in range(max_history + 5):
        msg = ConversationMessage(role=MessageRole.USER, message=f"msg {i}")
        session_manager.add_message(session.session_id, msg)

    updated = session_manager.get_session(session.session_id)
    assert len(updated.conversation_history) == max_history
    assert updated.conversation_history[0].message == f"msg {5}"


def test_context_variable_update():
    """Test updating context variables"""
    session = session_manager.create_session(SessionCreate())

    update = SessionUpdate(context_variables={"intent": "cancel", "order_id": "1234"})
    updated = session_manager.update_session(session.session_id, update)

    assert updated.context_variables["intent"] == "cancel"
    assert updated.context_variables["order_id"] == "1234"


def test_get_conversation_context():
    """Test conversation context string generation"""
    session = session_manager.create_session(SessionCreate())
    print("Session ID:", session.session_id)
    print(
        "Session exists:", session_manager.get_session(session.session_id) is not None
    )

    session_manager.add_message(
        session.session_id,
        create_user_message("Hi there!"),
    )
    session_manager.add_message(
        session.session_id,
        create_bot_message("Hello! How can I help?"),
    )
    session_manager.add_message(
        session.session_id,
        create_user_message("I'd like to cancel an order."),
    )

    context = session_manager.get_conversation_context(
        session.session_id, last_n_messages=3
    )

    print(f"\nContext:\n{context}")

    assert "User: Hi there!" in context
    assert "Alfred: Hello! How can I help?" in context
    assert "User: I'd like to cancel an order." in context


def test_extend_ttl():
    """Test session TTL extension"""
    session = session_manager.create_session(SessionCreate())

    key = session_manager.get_session_key(session.session_id)
    original_ttl = redis_client.connection.ttl(key)
    assert original_ttl > 0

    time.sleep(1)
    session_manager.extend_session_ttl(session.session_id)
    extended_ttl = redis_client.connection.ttl(key)

    assert extended_ttl > original_ttl - 1  # TTL should increase


def test_delete_session():
    """Test session deletion"""
    session = session_manager.create_session(SessionCreate())

    deleted = session_manager.delete_session(session.session_id)
    assert deleted is True

    retrieved = session_manager.get_session(session.session_id)
    assert retrieved is None


def test_get_active_session_count():
    """Test active session count"""
    initial_count = session_manager.get_active_session_count()
    session_manager.create_session(SessionCreate(user_id="one"))
    session_manager.create_session(SessionCreate(user_id="two"))

    new_count = session_manager.get_active_session_count()
    assert new_count == initial_count + 2


def test_get_session_not_found():
    """Test fetching non-existent session"""
    result = session_manager.get_session("nonexistent-id")
    assert result is None


def test_update_inactive_flag():
    """Test setting is_active to False"""
    session = session_manager.create_session(SessionCreate())
    session_manager.update_session(session.session_id, SessionUpdate(is_active=False))

    updated = session_manager.get_session(session.session_id)
    assert updated.is_active is False
