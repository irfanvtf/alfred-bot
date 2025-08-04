# Alfred Bot API Documentation

This document provides a summary of the API endpoints for the Alfred Bot.

## Base URL

`/api/v1`

---

### Chat Endpoints

| Method | Endpoint                             | Description                                       | Status Codes                | Authentication | Parameters                                                          |
| ------ | ------------------------------------ | ------------------------------------------------- | --------------------------- | -------------- | ------------------------------------------------------------------- |
| `POST` | `/chat`                              | Sends a message to the bot (session is optional). | `200 OK`, `400 Bad Request` | None           | `message` (required), `session_id` (optional), `user_id` (optional) |
| `POST` | `/chat/session/{session_id}`         | Sends a message within a specific session.        | `200 OK`, `404 Not Found`   | Session Token  | `message` (required)                                                |
| `GET`  | `/chat/stats`                        | Retrieves statistics for the chatbot engine.      | `200 OK`                    | Admin Token    | None                                                                |
| `GET`  | `/chat/session/{session_id}/context` | Retrieves the context and state for a session.    | `200 OK`, `404 Not Found`   | Session Token  | None                                                                |

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

| Method   | Endpoint                        | Description                                  | Status Codes                      | Authentication | Parameters                                           |
| -------- | ------------------------------- | -------------------------------------------- | --------------------------------- | -------------- | ---------------------------------------------------- |
| `POST`   | `/session/create`               | Creates a new session.                       | `200 OK`, `400 Bad Request`       | None           | `user_id` (optional), `context_variables` (optional) |
| `GET`    | `/session/{session_id}`         | Retrieves session data.                      | `200 OK`, `404 Not Found`         | Session Token  | None                                                 |
| `DELETE` | `/session/{session_id}`         | Deletes a session.                           | `204 No Content`, `404 Not Found` | Session Token  | None                                                 |
| `GET`    | `/session/{session_id}/summary` | Retrieves a brief summary of a session.      | `200 OK`, `404 Not Found`         | Session Token  | None                                                 |
| `POST`   | `/session/{session_id}/context` | Updates the context variables for a session. | `200 OK`, `404 Not Found`         | Session Token  | `context_variables` (required)                       |

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

| Method | Endpoint               | Description                                       | Status Codes | Authentication | Parameters |
| ------ | ---------------------- | ------------------------------------------------- | ------------ | -------------- | ---------- |
| `GET`  | `/health`              | General health check of the API.                  | `200 OK`     | None           | None       |
| `GET`  | `/health/redis`        | Checks the health of the Redis connection.        | `200 OK`     | None           | None       |
| `GET`  | `/health/chroma`       | Checks the health of the ChromaDB vector store.   | `200 OK`     | None           | None       |
| `GET`  | `/health/dependencies` | Runs a health check on all external dependencies. | `200 OK`     | None           | None       |
| `GET`  | `/health/stats`        | Retrieves comprehensive system statistics.        | `200 OK`     | Admin Token    | None       |

---

## Rate Limiting

All endpoints are subject to rate limiting. Please refer to the `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers in the API response for more information.
