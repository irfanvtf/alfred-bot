# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2024-07-10

### Added

- Structured fallback responses for unrecognized user queries to improve bot interactions
- Installation scripts for both Windows (PowerShell) and Unix (Bash) to simplify setup and management using Docker Compose

### Changed

- Updated knowledge base search configuration to require a higher confidence threshold for relevant answers
- Improved Docker Compose setup for the API service, including explicit startup commands and volume mapping
- Enhanced vector search service to utilize context-based filters for more accurate intent matching
- Updated Dockerfile for improved service startup and configuration

### Documentation

- Rewrote and expanded the main project README with comprehensive setup, usage, features, and developer guidance
- Added detailed roadmap, usage guide, API documentation, and product requirements documents
- Removed outdated documentation and changelog format guidelines

### Tests

- Removed multiple manual and integration test scripts, including environment setup, Redis connection, session management, vector search debugging, and API endpoint integration tests

## [0.7.0] - 2024-07-06

### Added

- Enhanced Knowledge Base: Comprehensive science-focused intents covering time and black holes, with content tailored for both kids and adults
- Session Continuity: Optional session ID field in chat requests for persistent conversation context
- Centralized Fallback System: Dedicated fallback knowledge base for more dynamic and consistent chatbot responses
- Performance Optimization: Knowledge base caching with status reporting for improved response times

### Changed

- Input Validation: Strengthened validation to reject empty or whitespace-only messages
- Message Processing: User messages now normalized to lowercase for consistency
- Service Reliability: Improved argument parsing and DNS resolution handling in startup scripts

### Fixed

- Service readiness checks now more reliable with better error handling

### Tests

- Model Testing: Extensive unit tests for chat and intent data models with robust input validation
- Vector Search Testing: New tests for confidence threshold filtering and vector search consistency
- Boundary Testing: Comprehensive coverage of edge cases and fallback scenarios

### Documentation

- Added detailed documentation for confidence threshold test coverage and manual verification procedures

## [0.6.0] - 2024-07-06

### Added

- Production-ready Docker support with multi-stage Dockerfile
- Docker Compose configurations for development and production
- Nginx setup for reverse proxy and load balancing
- Wait-for-it script for service readiness checks
- Comprehensive .dockerignore file to optimize Docker build contexts
- Documentation for recommended Docker production improvements and phased implementation plans

### Changed

- Improved code formatting and consistency in application initialization and API routes
- Enhanced exception handling in API routes to preserve original error context

### Security

- [List any security improvements here]

## [0.5.0] - 2024-07-04

### Added

- Comprehensive FastAPI-based API for chat interactions, session management, and health monitoring
- API endpoints organized under `/api/v1/` namespace
- Detailed health check endpoints for application, Redis, ChromaDB, and dependencies
- Integration tests covering API endpoints, middleware, and service integration

### Changed

- Updated dependencies and supporting modules for logging and middleware configuration

## [0.4.0] - 2024-07-01

### Added

- Session-aware chatbot engine with conversation flow management
- Intent classification and context-aware response system
- Conversation state tracking with templated responses
- Comprehensive automated and manual tests for chatbot engine and conversation state management
- Vector search scoring tests for improved accuracy

### Changed

- Improved test setup for easier module imports and debugging
- Updated test file paths and import structures for better maintainability

### Fixed

- Conversation context retrieval now includes full recent message history

## [0.3.0] - 2024-06-30

### Added

- Vector search system with support for Chroma backend
- Advanced intent matching and context-aware search capabilities
- Factory pattern for creating vector store instances
- Service layer for context-enhanced intent search
- Comprehensive tests for vector search and session context handling

### Changed

- Modularized vector store functionality for better maintainability and backward compatibility
- Updated field validation to use latest Pydantic decorators

### Fixed

- Improved file ignore patterns to exclude additional development artifacts and data files

## [0.2.0] - 2024-06-30

### Added

- Redis integration for individual chat session management
- Docker image configuration for Redis deployment
- System health check endpoint to monitor Redis connectivity and status

## [0.1.0] - 2024-06-26

### Added


- Text cleaning functionality including lemmatization and stop-word removal
- Knowledge base manager for interacting with JSON-stored intents and responses
- Initial project structure and core functionality
