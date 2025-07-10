# Alfred Bot API Documentation

This document provides detailed information about the API endpoints for the Alfred Bot.

## Base URL

The base URL for all API endpoints is:
`/api/v1`

---

## Endpoints

### 1. Chat

This is the main endpoint for interacting with the chatbot.

- **Endpoint**: `/chat`
- **Method**: `POST`
- **Description**: Sends a message to the chatbot and receives a response. If a `session_id` is provided, the bot will maintain conversation history. If not, a new session will be implicitly created.
- **Request Body**:

  ```json
  {
    "message": "Hello, who are you?",
    "session_id": "some-unique-session-id"
  }
  ```

  - `message` (string, required): The user's message to the bot.
  - `session_id` (string, optional): The unique identifier for the conversation session.

- **Example Request**:

  ```bash
  curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What is your purpose?"}'
  ```

- **Success Response (`200 OK`)**:
  ```json
  {
    "session_id": "some-unique-session-id",
    "response": "I am Alfred, a chatbot designed to assist you with information from our knowledge base.",
    "intent_id": "identity",
    "confidence": 0.95,
    "matched_query": "Who are you?"
  }
  ```

### 2. Session Management

This endpoint is used to explicitly create and manage user sessions.

- **Endpoint**: `/session`
- **Method**: `POST
- **Description**: Creates a new, empty session and returns a unique session ID.
- **Request Body**: None

- **Example Request**:

  ```bash
  curl -X POST http://localhost:8000/api/v1/session/
  ```

- **Success Response (`200 OK`)**:
  ```json
  {
    "session_id": "new-unique-session-id"
  }
  ```

### 3. Health Check

This endpoint is used to monitor the status of the application and its dependencies.

- **Endpoint**: `/health`
- **Method**: `GET`
- **Description**: Provides a health check of the API, including the status of the Redis connection.
- **Request Body**: None

- **Example Request**:

  ```bash
  curl -X GET http://localhost:8000/api/v1/health/
  ```

- **Success Response (`200 OK`)**:
  ```json
  {
    "status": "ok",
    "redis_status": "connected"
  }
  ```

### 4. Chat Service Stats

This endpoint retrieves configuration and statistics about the chatbot engine.

- **Endpoint**: `/chat/stats`
- **Method**: `GET`
- **Description**: Returns internal statistics and configuration details of the vector search service, such as the confidence threshold.
- **Request Body**: None

- **Example Request**:

  ```bash
  curl -X GET http://localhost:8000/api/v1/chat/stats | jq .
  ```

- **Success Response (`200 OK`)**:
  ```json
  {
    "stats": {
      "vector_service": {
        "service_config": {
          "model_name": "en_core_web_md",
          "confidence_threshold": 0.25
        },
        "knowledge_base_stats": {
          "total_intents": 15,
          "last_updated": "2025-07-09T10:00:00Z"
        }
      }
    }
  }
  ```
  No newline at end of file
