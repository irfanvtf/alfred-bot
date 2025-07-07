# Alfred Bot Production Dockerfile
# Multi-stage build for optimal size and security

# Build stage
FROM python:3.11-slim AS builder

# Set build arguments
ARG BUILDPLATFORM
ARG TARGETPLATFORM

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
WORKDIR /app
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy models
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download en_core_web_md

# Production stage
FROM python:3.11-slim AS production

# Set metadata
LABEL maintainer="Irfan Murad <irfanfmurad@gmail.com>"
LABEL description="Alfred Bot - Local Assistant Bot"
LABEL version="1.0.0"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends     curl     ca-certificates     netcat-traditional     && rm -rf /var/lib/apt/lists/*     && apt-get clean

# Create non-root user for security
RUN groupadd -r alfred && useradd -r -g alfred alfred

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=alfred:alfred . .
COPY --chown=alfred:alfred docker/wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh

# Create necessary directories with proper permissions
RUN mkdir -p logs data/chroma_db config \
    && chown -R alfred:alfred /app

# Create .env file from environment variables if it doesn't exist
RUN touch .env && chown alfred:alfred .env

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Application configuration
ENV API_TITLE="Alfred Chatbot API"
ENV API_VERSION="v1"
ENV API_HOST=0.0.0.0
ENV API_PORT=8000

# Logging configuration
ENV LOG_LEVEL=INFO
ENV LOG_TO_FILE=true

# Redis configuration
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV REDIS_DB=0
ENV REDIS_DECODE_RESPONSES=true

# Session configuration
ENV SESSION_TTL=3600
ENV MAX_CONVERSATION_HISTORY=50

# Chatbot configuration
ENV SIMILARITY_THRESHOLD=0.7
ENV MAX_RESULTS=5

# spaCy configuration
ENV SPACY_MODEL_MD=en_core_web_md
ENV SPACY_MODEL_SM=en_core_web_sm

# Vector database configuration
ENV CHROMA_PERSIST_DIRECTORY=/app/data/chroma_db
ENV PINECONE_INDEX_NAME=chatbot-knowledge

# These should be set via docker-compose.yml or docker run for security
# ENV PINECONE_API_KEY=your_api_key_here
# ENV PINECONE_ENVIRONMENT=your_environment_here

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user
USER alfred

# Expose port
EXPOSE 8000

# Start command
CMD ["wait-for-it.sh", "redis:6379", "--", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]