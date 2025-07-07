# Confidence Threshold Test Coverage

## Overview

This document describes the test coverage added for the confidence threshold change from the default to 0.25 in `src/services/vector_store/search_service.py`.

## Changes Made

### 1. Vector Search Service (src/services/vector_store/search_service.py)
- **Line 20**: `self.confidence_threshold = 0.25` 
- This lowered the default confidence threshold from a higher value to 0.25

### 2. Test Coverage Added (tests/test_vector_search.py)

#### New Test Methods:

1. **`test_confidence_threshold_filtering()`**
   - **Purpose**: Verifies that the 0.25 confidence threshold is correctly applied
   - **Tests**:
     - High confidence queries (≥0.25) return results
     - Low confidence queries (<0.25) are filtered out
     - All returned results meet the threshold requirement
   - **Test Cases**:
     - `"hello"` → should match `greeting` intent (high confidence)
     - `"hi there"` → should match `greeting` intent (high confidence)  
     - `"help me please"` → should match `help` intent (high confidence)
     - `"xyzabc123nonsense"` → should be filtered out (low confidence)
     - `"completely unrelated random text"` → should be filtered out (low confidence)

2. **`test_borderline_confidence_scores()`**
   - **Purpose**: Tests behavior around the exact 0.25 threshold boundary
   - **Tests**:
     - Queries that might produce scores near the threshold
     - Verifies that only results ≥0.25 are returned
     - Identifies and logs borderline scores (0.24-0.26 range)
   - **Test Cases**:
     - `"hi"`, `"help"`, `"thank"`, `"bye"`, `"weather info"`

3. **`test_confidence_threshold_consistency()`**
   - **Purpose**: Ensures threshold consistency across service methods
   - **Tests**:
     - Service instance has `confidence_threshold = 0.25`
     - Stats endpoint reports the correct threshold value

### 3. Documentation Update (data/knowledge-base.json)

Added `search_config` section to metadata:
```json
"search_config": {
  "default_confidence_threshold": 0.25,
  "note": "The vector search service uses a default confidence threshold of 0.25. Individual intents can override this with their own confidence_threshold value. Queries scoring below the threshold are filtered out."
}
```

## Test Verification

### Manual Verification Commands:

1. **Check service threshold**:
   ```bash
   curl -X GET http://localhost:8000/api/v1/chat/stats | jq '.stats.vector_service.service_config.confidence_threshold'
   ```
   Expected: `0.25`

2. **Test low confidence query (should fallback)**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat/ -H "Content-Type: application/json" -d '{"message": "xyzabc123randomnonsense"}'
   ```
   Expected: `"intent_id": "fallback"`, `"confidence": 0.0`

3. **Test high confidence query (should match)**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat/ -H "Content-Type: application/json" -d '{"message": "hello"}'
   ```
   Expected: `"intent_id": "greeting"`, `"confidence": 0.7` (or similar high value)

## Test Behavior

### Filtering Logic
The search service applies filtering in `search_intents()` method:
```python
if score >= threshold:
    # Add context-aware scoring
    context_score = self._calculate_context_score(result, session_context)
    result["final_score"] = (score * 0.7) + (context_score * 0.3)
    result["context_score"] = context_score
    filtered_results.append(result)
```

### Threshold Sources
1. **Default**: `self.confidence_threshold = 0.25` (service level)
2. **Per-intent**: `metadata.confidence_threshold` (intent level)
3. **Priority**: Intent-level threshold overrides service default

## Expected Test Results

### ✅ Should Pass Threshold (≥0.25):
- Exact pattern matches
- Close semantic matches
- Well-formed queries related to known intents

### ❌ Should Be Filtered (<0.25):
- Random nonsense text
- Completely unrelated queries
- Very poor semantic matches

## Impact

This change allows more queries to pass through to intent matching while still filtering out truly irrelevant queries, improving the chatbot's responsiveness while maintaining quality control.

## Running Tests

To run the specific confidence threshold tests:

```bash
# Run specific test methods (requires pytest)
python -m pytest tests/test_vector_search.py::TestVectorSearch::test_confidence_threshold_filtering -v
python -m pytest tests/test_vector_search.py::TestVectorSearch::test_borderline_confidence_scores -v  
python -m pytest tests/test_vector_search.py::TestVectorSearch::test_confidence_threshold_consistency -v

# Run all vector search tests
python -m pytest tests/test_vector_search.py -v
```

## Notes

- Tests are designed to be robust against different embedding models
- The actual confidence scores may vary depending on the spaCy model used
- Tests focus on relative behavior (above/below threshold) rather than exact score values
- Manual verification using API endpoints provides additional confidence in the implementation
