#!/usr/bin/env python3
# manual_test_chatbot.py
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from src.services.chatbot_engine import chatbot_engine


def test_chatbot_manually():
    """Manual test of the chatbot engine"""
    print("=== Manual Chatbot Engine Test ===\n")

    # Test 1: Simple greeting
    print("1. Testing greeting...")
    message = "hello"
    response = chatbot_engine.process_message(message)
    print(f"Input: {message}")
    print(f"Response: {response.response}")
    print(f"Intent ID: {response.intent_id}")
    print(f"Confidence: {response.confidence}")
    print(f"Metadata: {response.metadata}")
    print()

    # Test 2: Get engine stats
    print("2. Engine stats...")
    stats = chatbot_engine.get_engine_stats()
    print(f"Engine stats: {stats}")
    print()

    # Test 3: Test with same session
    session_id = response.metadata.get("session_id")
    if session_id:
        print(f"3. Testing with same session ({session_id})...")
        message = "thank you"
        response2 = chatbot_engine.process_message(message, session_id=session_id)
        print(f"Input: {message}")
        print(f"Response: {response2.response}")
        print(f"Intent ID: {response2.intent_id}")
        print(f"Confidence: {response2.confidence}")
        print()

        # Check conversation state
        state = chatbot_engine.get_conversation_state(session_id)
        print(f"Conversation state: {state}")

    print("=== Test completed ===")


if __name__ == "__main__":
    test_chatbot_manually()
