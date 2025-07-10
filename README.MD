ALFRED CHATBOT

# Alfred Chatbot

Alfred Bot is a session-aware, knowledge-based chatbot built with Python, FastAPI, and spaCy. It uses a vector store (ChromaDB) for intent matching and Redis for session management.

## Features

- **Session-aware conversations**: Maintains conversation history for context-aware responses.
- **Knowledge-based responses**: Retrieves answers from a knowledge base using vector-based similarity search.
- **FastAPI backend**: A modern, fast (high-performance) web framework for building APIs.
- **Vector Search**: Utilizes spaCy for natural language processing and ChromaDB for efficient vector storage and retrieval.
- **Redis Session Management**: Manages user sessions for a personalized experience.
- **Dockerized**: Comes with Docker and Docker Compose configurations for easy setup and deployment.
- **Extensible**: The project is structured to be easily extended with new features and knowledge.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: Version 3.8 or higher.
- **Docker and Docker Compose**: For running the application in a containerized environment.
- **Redis**: An active Redis instance is required for session management. You can run this locally or use the provided Docker Compose setup.

## Getting Started

For detailed installation and setup instructions, please see the [Usage Guide](./docs/USAGE.md).

For details on the API endpoints, see the [API Documentation](./docs/API.md).

## Running Tests

To run the tests, use the following command:

```bash
pytest
```

## Project Structure

```
alfred-bot/
├── config/                  # Configuration files
├── data/                    # Knowledge base and system data
├── docker/                  # Docker setup and deployment
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── src/                     # Main source code
│   ├── api/                 # FastAPI routes and middleware
│   ├── models/              # Data models and schemas
│   ├── services/            # Core business logic
│   └── utils/               # Helper functions
├── tests/                   # Unit and integration tests
├── main.py                  # Application entry point
├── requirements.txt
└── README.md
```

## Dependencies

The main dependencies of this project are:

- **FastAPI**: For building the API.
- **Uvicorn**: For running the FastAPI application.
- **spaCy**: For natural language processing.
- **ChromaDB**: For vector storage and similarity search.
- **Redis**: For session management.
- **Pydantic**: For data validation.

For a full list of dependencies, see `requirements.txt`.

## Current Status and Future Improvements

The project has completed its core development phases, including the FastAPI integration, vector search, and session management. The immediate focus is on enhancing the knowledge management capabilities and improving the testing framework.

Future improvements will focus on adding an analytics dashboard, advanced context handling, and integrations with external services. For a detailed view of the project's direction, please see the [Roadmap](./docs/ROADMAP.md).
