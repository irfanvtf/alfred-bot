#!/usr/bin/env python3
"""
Comprehensive test script for validating intent matching in Alfred Bot.
This script tests all intents and patterns defined in the dialog-en.json file
by calling the /api/v1/chat endpoint and asserting the correct intent responses.
"""

import json
import requests
import time
from typing import Dict, List, Tuple

# Configuration
API_BASE_URL = "http://localhost:8000/api/v1"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"
DIALOG_FILE_PATH = "data/sources/en/dialog-en.json"

# Test results tracking
test_results = {"passed": 0, "failed": 0, "total": 0}


def load_dialog_data() -> Dict:
    """Load dialog data from JSON file"""
    with open(DIALOG_FILE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_intents_and_patterns(dialog_data: Dict) -> List[Tuple[str, str, str]]:
    """
    Extract all intent IDs, patterns, and expected responses from dialog data

    Returns:
        List of tuples (intent_id, pattern, response_id)
    """
    test_cases = []

    for intent in dialog_data.get("intents", []):
        intent_id = intent.get("id")
        patterns = intent.get("patterns", [])
        responses = intent.get("responses", [])

        # For each pattern, we'll test with the first response
        # In a real scenario, any of the responses would be valid
        if patterns and responses:
            response_id = responses[0].get("id")
            for pattern in patterns:
                test_cases.append((intent_id, pattern, response_id))

    return test_cases


def test_intent_matching(
    intent_id: str, pattern: str, expected_response_id: str
) -> bool:
    """
    Test if a given pattern correctly matches to its intent

    Args:
        intent_id: Expected intent ID
        pattern: User input pattern to test
        expected_response_id: Expected response ID

    Returns:
        True if test passes, False otherwise
    """
    try:
        # Prepare request payload
        payload = {
            "message": pattern,
            "session_id": f"test_session_{int(time.time() * 1000000)}",
            "user_id": "test_user",
        }

        # Make API call
        response = requests.post(CHAT_ENDPOINT, json=payload)

        # Check if request was successful
        if response.status_code != 200:
            print(f"❌ FAILED: Pattern '{pattern}' - HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        # Parse response
        response_data = response.json()
        matched_intent = response_data.get("intent_id")
        response_id = response_data.get("response_id")

        # Check if intent matches
        if matched_intent == intent_id:
            print(f"✅ PASSED: Pattern '{pattern}' -> Intent '{intent_id}'")
            return True
        else:
            print(f"❌ FAILED: Pattern '{pattern}'")
            print(f"   Expected intent: {intent_id}")
            print(f"   Actual intent:   {matched_intent}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ FAILED: Pattern '{pattern}' - Request error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ FAILED: Pattern '{pattern}' - JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Pattern '{pattern}' - Unexpected error: {e}")
        return False


def run_comprehensive_intent_tests():
    """Run tests for all intents and patterns"""
    print("🧪 Starting comprehensive intent matching tests...\n")

    # Load dialog data
    try:
        dialog_data = load_dialog_data()
        print(
            f"📚 Loaded dialog data with {len(dialog_data.get('intents', []))} intents"
        )
    except Exception as e:
        print(f"❌ Failed to load dialog data: {e}")
        return

    # Extract test cases
    test_cases = extract_intents_and_patterns(dialog_data)
    print(f"📋 Extracted {len(test_cases)} test cases\n")

    # Run each test case
    for intent_id, pattern, expected_response_id in test_cases:
        test_results["total"] += 1
        if test_intent_matching(intent_id, pattern, expected_response_id):
            test_results["passed"] += 1
        else:
            test_results["failed"] += 1

    # Print summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"Total tests:  {test_results['total']}")
    print(f"Passed:       {test_results['passed']}")
    print(f"Failed:       {test_results['failed']}")
    print(
        f"Success rate: {test_results['passed'] / test_results['total'] * 100:.1f}%"
        if test_results["total"] > 0
        else "No tests run"
    )

    # Return success status
    return test_results["failed"] == 0


def main():
    """Main function to run the test suite"""
    print("🚀 Alfred Bot - Intent Matching Test Suite (English)")
    print("=" * 50)

    # Check if API is accessible
    try:
        response = requests.get(f"{API_BASE_URL}/docs")
        if response.status_code != 200:
            print(
                "⚠️  Warning: API documentation not accessible. API might not be running."
            )
    except requests.exceptions.RequestException:
        print(
            "❌ Error: Could not connect to API. Please ensure the API is running at",
            API_BASE_URL,
        )
        return

    # Run tests
    success = run_comprehensive_intent_tests()

    # Exit with appropriate code
    if success:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)


if __name__ == "__main__":
    main()
