# Alfred Bot API Documentation

This document provides a summary of the API endpoints for the Alfred Bot.

## Base URL

`/api/v1`

---

### Chat Endpoints

| Method | Endpoint                             | Description                                           |
|--------|--------------------------------------|-------------------------------------------------------|
| `POST` | `/chat`                              | Sends a message to the bot (session is optional).     |
| `POST` | `/chat/session/{session_id}`         | Sends a message within a specific session.            |
| `GET`  | `/chat/stats`                        | Retrieves statistics for the chatbot engine.          |
| `GET`  | `/chat/session/{session_id}/context` | Retrieves the context and state for a session.        |

#### Example: `POST /chat`

**Request Body:**
```json
{
  "message": "Hello, who are you?",
  "session_id": "optional-session-id",
  "user_id": "optional-user-id"
}
```

**Success Response (`200 OK`):**
```json
{
  "session_id": "some-unique-session-id",
  "response": "I am Alfred, a chatbot designed to assist you.",
  "intent_id": "identity",
  "confidence": 0.95,
  "matched_query": "Who are you?"
}
```

---

### Session Management Endpoints

| Method   | Endpoint                      | Description                                      |
|----------|-------------------------------|--------------------------------------------------|
| `POST`   | `/session/create`             | Creates a new session.                           |
| `GET`    | `/session/{session_id}`       | Retrieves session data.                          |
| `DELETE` | `/session/{session_id}`       | Deletes a session.                               |
| `GET`    | `/session/{session_id}/summary` | Retrieves a brief summary of a session.          |
| `POST`   | `/session/{session_id}/context` | Updates the context variables for a session.     |

#### Example: `POST /session/create`

**Request Body:**
```json
{
  "user_id": "optional-user-id",
  "context_variables": {
    "initial_data": "value"
  }
}
```

**Success Response (`200 OK`):**
```json
{
  "session_id": "new-unique-session-id",
  "user_id": "optional-user-id",
  "context_variables": { "initial_data": "value" },
  "conversation_history": [],
  "last_activity": "2025-08-04T12:00:00Z"
}
```

---

### Health Check Endpoints

| Method | Endpoint                 | Description                                      |
|--------|--------------------------|--------------------------------------------------|
| `GET`  | `/health`                | General health check of the API.                 |
| `GET`  | `/health/redis`          | Checks the health of the Redis connection.       |
| `GET`  | `/health/chroma`         | Checks the health of the ChromaDB vector store.  |
| `GET`  | `/health/dependencies`   | Runs a health check on all external dependencies.|
| `GET`  | `/health/stats`          | Retrieves comprehensive system statistics.       |
