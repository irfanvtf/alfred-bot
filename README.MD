# Alfred Chatbot

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Project Version](https://img.shields.io/badge/version-0.8.0-blue.svg)](pyproject.toml)

Alfred Bot is a session-aware, knowledge-based chatbot built with Python, FastAPI, and sentence-transformers. It uses a vector store (ChromaDB) for intent matching and Redis for session management.

## Features

- **Session-aware conversations**: Maintains conversation history for context-aware responses.
- **Knowledge-based responses**: Retrieves answers from a knowledge base using vector-based similarity search.
- **FastAPI backend**: A modern, fast (high-performance) web framework for building APIs.
- **Vector Search**: Utilizes natural language processing and ChromaDB for efficient vector storage and retrieval.
- **Redis Session Management**: Manages user sessions for a personalized experience.
- **Dockerized**: Comes with Docker and Docker Compose configurations for easy setup and deployment.
- **Extensible**: The project is structured to be easily extended with new features and knowledge.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python**: Version 3.11 or higher (as specified in `pyproject.toml`).
- **Docker and Docker Compose**: For running the application in a containerized environment.
- **Redis**: An active Redis instance is required for session management. You can run this locally or use the provided Docker Compose setup.

## Getting Started

For detailed installation and setup instructions, please see the [Usage Guide](./docs/usage.md).

For details on the API endpoints, see the [API Documentation](./docs/api.md).

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

This project manages its dependencies using `pyproject.toml`. The core application dependencies are listed under the `[project.dependencies]` section.

Key dependencies include:

- **FastAPI**: For the web framework.
- **Uvicorn**: As the ASGI server.
- **Sentence-Transformers**: For generating text embeddings.
- **ChromaDB**: For vector storage and search.
- **Redis**: For session management.
- **Pydantic**: For data modeling and validation.

For a complete and versioned list of dependencies required for production, please see the `requirements.txt` file. For development and testing dependencies, refer to the `[project.optional-dependencies]` section in `pyproject.toml`.

## Current Status and Future Improvements

The project has completed its core development phases, including the FastAPI integration, vector search, and session management. The immediate focus is on enhancing the knowledge management capabilities and improving the testing framework.

Future improvements will focus on adding an analytics dashboard, advanced context handling, and integrations with external services. For a detailed view of the project's direction, please see the [Roadmap](./docs/roadmap.md).
