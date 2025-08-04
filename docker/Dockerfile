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

# Download sentence transformer models (pre-bake them)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
# Optional: Download backup model for better quality if needed
# RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-mpnet-base-v2')"

# Production stage
FROM python:3.11-slim AS production

# Set metadata
LABEL maintainer="Irfan Murad <irfanfmurad@gmail.com>"
LABEL description="Alfred Bot - Local Assistant Bot with BERT"
LABEL version="1.1.0"

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    netcat-traditional \
    dnsutils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy wait-for-it script BEFORE creating user (as root)
COPY docker/wait-for-it.sh /usr/local/bin/wait-for-it.sh
RUN chmod +x /usr/local/bin/wait-for-it.sh

# Create non-root user for security
RUN groupadd -r alfred && useradd -r -g alfred alfred

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy model caches from builder stage 
COPY --from=builder /root/.cache /home/alfred/.cache
RUN chown -R alfred:alfred /home/alfred/.cache

# Copy application code (as root, then change ownership)
COPY . .
RUN chown -R alfred:alfred /app

# Create necessary directories with proper permissions
RUN mkdir -p logs data/chroma_db config \
    && chown -R alfred:alfred logs data config

# Create .env file from environment variables if it doesn't exist
RUN touch .env && chown alfred:alfred .env

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Switch to non-root user (AFTER copying files that need root privileges)
USER alfred

# Expose port
EXPOSE 8000

# Start command
CMD ["wait-for-it.sh", "redis:6379", "--", "python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]