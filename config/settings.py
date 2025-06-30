import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    # Pinecone configuration
    pinecone_api_key: str = os.getenv("PINECONE_API_KEY", "")
    pinecone_environment: str = os.getenv("PINECONE_ENVIRONMENT", "")
    pinecone_index_name: str = os.getenv("PINECONE_INDEX_NAME", "chatbot-knowledge")

    # spaCy configuration
    spacy_model_md: str = os.getenv("SPACY_MODEL_MD", "en_core_web_md")
    spacy_model_sm: str = os.getenv("SPACY_MODEL_SM", "en_core_web_sm")

    # API configuration
    api_title: str = os.getenv("API_TITLE", "")
    api_version: str = os.getenv("API_VERSION", "")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    # Chatbot configuration
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.7"))
    max_results: int = int(os.getenv("MAX_RESULTS", "5"))

    # Redis configuration
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = os.getenv("REDIS_PORT", 6379)
    redis_db: int = os.getenv("REDIS_DB", 0)
    redis_password: Optional[str] = None
    redis_decode_responses: bool = os.getenv("REDIS_DECODE_RESPONSES", True)

    # Session settings
    session_ttl: int = os.getenv("SESSION_TTL", 3600)
    max_conversation_history: int = os.getenv("MAX_CONVERSATION_HISTORY", 50)

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
