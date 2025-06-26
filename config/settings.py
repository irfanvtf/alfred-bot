# config/settings.py - Simplified version without pydantic-settings
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    # Pinecone Configuration
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "chatbot-knowledge")

    # spaCy Configuration
    spacy_model: str = os.getenv("SPACY_MODEL", "en_core_web_md")

    # API Configuration
    api_title: str = os.getenv("API_TITLE", "")
    api_version: str = os.getenv("API_VERSION", "")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # Chatbot Configuration
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    max_results: int = int(os.getenv("MAX_RESULTS", "5"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def validate(self):
        """Validate required settings"""
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY is required")
        if not self.pinecone_environment:
            raise ValueError("PINECONE_ENVIRONMENT is required")


settings = Settings()

# Validate settings on import (optional)
# settings.validate()
