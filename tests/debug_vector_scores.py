#!/usr/bin/env python3
# debug_vector_scores.py
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.chatbot_engine import chatbot_engine


def debug_vector_scores():
    """Debug vector search scores"""
    print("=== Debug Vector Search Scores ===\n")

    # Test queries
    test_queries = [
        "hello",
        "hi",
        "hey",
        "good morning",
        "thank you",
        "goodbye",
        "help me",
        "random query that should not match",
    ]

    for query in test_queries:
        print(f"Query: '{query}'")

        # Get intent matches directly from vector service
        session_context = {"conversation_state": "greeting", "message_count": 0}
        intent_matches = chatbot_engine._classify_intent(query, session_context)

        if intent_matches:
            print(f"  Found {len(intent_matches)} matches:")
            for i, match in enumerate(intent_matches[:3]):  # Show top 3
                print(f"    {i + 1}. Intent: {match['intent_id']}")
                print(f"       Confidence: {match['confidence']:.3f}")
                print(f"       Original Score: {match['original_score']:.3f}")
                print(f"       Context Score: {match['context_score']:.3f}")
                print(f"       Pattern: '{match['matched_pattern']}'")
                print(f"       Category: {match['category']}")
        else:
            print("  No matches found")

        print()


if __name__ == "__main__":
    debug_vector_scores()
