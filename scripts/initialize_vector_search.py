# scripts/initialize_vector_search.py
"""
Script to initialize and test the vector search system
Run this after setting up the vector store implementation
"""

import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.services.vector_store import VectorSearchService
from src.services.knowledge_manager import KnowledgeManager
from src.utils.exceptions import ConfigurationError


def main():
    """Initialize vector search and test it"""
    print("🚀 Initializing Alfred Vector Search System")
    print("=" * 50)

    try:
        # Initialize services
        print("1. Loading knowledge base...")
        km = KnowledgeManager()
        knowledge_base = km.load_knowledge_base()
        print(f"   ✅ Loaded {len(knowledge_base.intents)} intents")

        # Initialize vector search (using Chroma for prototype)
        print("\n2. Initializing vector search service...")
        vector_service = VectorSearchService(use_chroma=True)
        vector_service.initialize()
        print("   ✅ Vector service initialized")

        # Index knowledge base
        print("\n3. Indexing knowledge base...")
        vector_service.index_knowledge_base(knowledge_base.model_dump())

        # Get stats
        print("\n4. Getting system statistics...")
        stats = vector_service.get_stats()
        print(f"   Vector Store: {stats['vector_store']['store_type']}")
        print(f"   Vectors Indexed: {stats['vector_store']['vector_count']}")
        print(f"   Text Processor: {stats['text_processor']['model_name']}")
        print(f"   Vector Dimension: {stats['text_processor']['vector_size']}")

        # Test search functionality
        print("\n5. Testing search functionality...")
        test_queries = [
            "hello there",
            "can you help me",
            "thank you very much",
            "what's the weather like",
            "goodbye",
        ]

        for query in test_queries:
            print(f"\n   Query: '{query}'")
            results = vector_service.search_intents(query, top_k=3)

            if results:
                for i, result in enumerate(results[:2], 1):
                    intent_id = result["metadata"]["intent_id"]
                    score = result.get("final_score", result.get("score", 0))
                    print(f"     {i}. Intent: {intent_id} (Score: {score:.3f})")
            else:
                print("     No matches found")

        # Test with session context
        print("\n6. Testing with session context...")
        session_context = {
            "conversation_history": [
                {
                    "role": "user",
                    "message": "hello",
                    "timestamp": "2024-01-01T10:00:00",
                },
                {
                    "role": "bot",
                    "message": "Hello! How can I help?",
                    "timestamp": "2024-01-01T10:00:01",
                },
            ],
            "context_variables": {
                "last_intent": "greeting",
                "last_category": "greeting",
            },
        }

        context_query = "thanks for the help"
        print(f"   Context Query: '{context_query}'")
        context_results = vector_service.search_intents(
            context_query, session_context=session_context
        )

        if context_results:
            result = context_results[0]
            intent_id = result["metadata"]["intent_id"]
            base_score = result.get("score", 0)
            context_score = result.get("context_score", 0)
            final_score = result.get("final_score", 0)
            print(f"     Intent: {intent_id}")
            print(f"     Base Score: {base_score:.3f}")
            print(f"     Context Score: {context_score:.3f}")
            print(f"     Final Score: {final_score:.3f}")

        # Test fallback
        print("\n7. Testing fallback response...")
        fallback = vector_service.get_fallback_response("something completely random")
        print(f"   Fallback: {fallback['response']}")

        print("\n" + "=" * 50)
        print("✅ Vector Search System Successfully Initialized!")
        print("🎯 Ready for Phase 5: Core Chatbot Logic")

    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e}")
        print("\n💡 Troubleshooting:")
        print("   - Make sure chromadb is installed: pip install chromadb")
        print("   - Check that your knowledge base file exists")
        print("   - Verify spaCy model is installed")

    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
