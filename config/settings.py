import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
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

    # Chroma configuration
    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def validate(self):
        """Validate required settings"""
        if not self.api_title:
            raise ValueError("API_TITLE must be set")

        # Ensure numeric env vars are really numeric
        try:
            self.api_port = int(self.api_port)
            self.redis_port = int(self.redis_port)
            self.redis_db = int(self.redis_db)
            self.session_ttl = int(self.session_ttl)
            self.max_results = int(self.max_results)
            self.similarity_threshold = float(self.similarity_threshold)
        except ValueError as exc:
            raise ValueError("Invalid numeric environment variable") from exc


settings = Settings()

# Validate settings on import (optional)
# settings.validate()
