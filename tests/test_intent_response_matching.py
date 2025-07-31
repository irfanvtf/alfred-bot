#!/usr/bin/env python3
"""
Script to test intent responses against an API endpoint.
Reads intent-response pairs from JSON and validates API responses.
"""

import json
import requests
import sys
from typing import List, Dict, Any
from urllib.parse import urljoin

# Configuration
API_BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/v1/chat"
TIMEOUT = 10  # Request timeout in seconds


def load_intent_data(file_path: str) -> List[Dict[str, Any]]:
    """Load intent-response data from JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{file_path}': {e}")
        sys.exit(1)


def get_json_file_path():
    """Get the path to the intent_responses.json file."""
    import os

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(project_root, "data", "intent_responses.json")


def call_api(intent: str, message: str = None) -> str:
    """
    Call the API endpoint with the intent as the message.

    Args:
        intent: The intent identifier (will be used as the message)
        message: Not used, kept for compatibility

    Returns:
        The API response text
    """
    url = urljoin(API_BASE_URL, ENDPOINT)

    # Use the intent as the message to send to the API
    payload = {
        "message": intent,
        "session_id": "test_session",
        "user_id": "test_user",
        "context": {},
    }

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()

        # Parse the ChatResponse and extract only the "response" field
        response_data = response.json()

        if "response" in response_data:
            return response_data["response"]
        else:
            return f"API_ERROR: 'response' field not found in API response"

    except requests.exceptions.RequestException as e:
        return f"API_ERROR: {str(e)}"
    except json.JSONDecodeError:
        return f"API_ERROR: Invalid JSON response"
    except Exception as e:
        return f"API_ERROR: {str(e)}"


def normalize_text(text: str) -> str:
    """Normalize text for comparison (remove extra whitespace, convert to lowercase)."""
    return " ".join(text.strip().lower().split())


def check_response_match(actual: str, expected_responses: List[str]) -> bool:
    """
    Check if the actual response matches any of the expected responses.

    Args:
        actual: The actual API response
        expected_responses: List of expected response texts

    Returns:
        True if there's a match, False otherwise
    """
    if actual.startswith("API_ERROR:"):
        return False

    actual_normalized = normalize_text(actual)

    for expected in expected_responses:
        expected_normalized = normalize_text(expected)
        if actual_normalized == expected_normalized:
            return True

    return False


def main():
    """Main function to run the intent response checker."""

    # Get the JSON file path based on project structure
    json_file = get_json_file_path()

    print("Loading intent data...")
    intent_data = load_intent_data(json_file)

    print(f"Testing {len(intent_data)} intents against {API_BASE_URL}{ENDPOINT}")
    print("=" * 80)

    mismatches = []
    api_errors = []
    total_tests = len(intent_data)
    passed_tests = 0

    for i, item in enumerate(intent_data, 1):
        intent = item["intent"]
        expected_responses = item["responses"]

        print(f"[{i}/{total_tests}] Testing intent: {intent}")

        # Call the API
        actual_response = call_api(intent)

        # Check for API errors
        if actual_response.startswith("API_ERROR:"):
            api_errors.append({"intent": intent, "error": actual_response})
            print(f"  ❌ API Error: {actual_response}")
            continue

        # Check if response matches
        if check_response_match(actual_response, expected_responses):
            print(f"  ✅ Match found")
            passed_tests += 1
        else:
            mismatches.append(
                {
                    "intent": intent,
                    "expected": expected_responses,
                    "actual": actual_response,
                }
            )
            print(f"  ❌ No match")

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.2f}%")
    print(f"Failed (mismatches): {len(mismatches)}")
    print(f"Failed (API errors): {len(api_errors)}")

    # Print API errors
    if api_errors:
        print(f"\n🚨 API ERRORS ({len(api_errors)}):")
        print("-" * 40)
        for error in api_errors:
            print(f"Intent: {error['intent']}")
            print(f"Error: {error['error']}")
            print()

    # Print mismatches
    if mismatches:
        print(f"\n❌ RESPONSE MISMATCHES ({len(mismatches)}):")
        print("-" * 40)
        for mismatch in mismatches:
            print(f"Intent: {mismatch['intent']}")
            print(f"Expected responses:")
            for i, expected in enumerate(mismatch["expected"], 1):
                print(f'  {i}. "{expected}"')
            print(f'Actual response: "{mismatch["actual"]}"')
            print()

    # Exit with appropriate code
    if mismatches or api_errors:
        sys.exit(1)
    else:
        print("🎉 All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
