# main.py - Phase 6: FastAPI Integration Complete
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from config.settings import settings

# Import API routes
from src.api.routes.chat import router as chat_router
from src.api.routes.session import router as session_router
from src.api.routes.health import router as health_router
from src.api.routes.chroma import router as chroma_router, get_chroma_service

# Import middleware and error handling
from src.api.middleware import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    setup_exception_handlers,
)

# Import logging configuration
from src.utils.logging_config import setup_logging

# Import data loading function
from src.services.data_loader import (
    initialize_all_knowledge_collections,
    LANGUAGE_CONFIG,
)

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Setup logging
log_level = os.getenv("LOG_LEVEL", "DEBUG")  # Changed to DEBUG for more detailed logs
log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
setup_logging(log_level=log_level, log_to_file=log_to_file)

# Initialize all knowledge collections at startup
# This should be done before the FastAPI app is created to ensure all collections are ready.
print("Initializing knowledge collections...")
logger.info("Starting knowledge collection initialization...")
try:
    initialize_all_knowledge_collections(
        persist_path=settings.chroma_persist_directory,  # Use setting from config
        languages=LANGUAGE_CONFIG,  # Use the config defined in data_loader.py
    )
    print("Knowledge collections initialized successfully.")
    logger.info("Knowledge collections initialized successfully.")
except Exception as e:
    print(f"Failed to initialize knowledge collections: {e}")
    logger.error(f"Failed to initialize knowledge collections: {e}", exc_info=True)
    # Depending on your requirements, you might want to exit here if initialization is critical
    # import sys
    # sys.exit(1)


# Get configuration from environment variables
# TODO: update versioning to use pyproject.toml (dynamic)
# TODO: add app version as well
API_TITLE = os.getenv("API_TITLE", "Alfred Chatbot API")
API_VERSION = os.getenv("API_VERSION", "1.0.0")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="A session-aware knowledge-based chatbot using sentence-transformers and ChromaDB",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(LoggingMiddleware)

# Setup exception handlers
setup_exception_handlers(app)


# Initialize embedding function during startup to prevent model download during first query
@app.on_event("startup")
async def initialize_embedding_model():
    """Initialize the embedding model during startup to prevent download during first query."""
    logger.info("Initializing embedding model...")
    try:
        # Initialize the text processor which will load the model
        from src.services.text_processor import text_processor

        # Trigger model loading by calling the model with a dummy text
        text_processor.get_text_vector("preload")
        print("Embedding model initialized successfully.")
    except Exception as e:
        print(f"Warning: Failed to initialize embedding model during startup: {e}")
        # This is not critical, as queries can still work, but they might trigger the download


# Include API routers
app.include_router(chat_router, prefix="/api/v1")
app.include_router(session_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(chroma_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Alfred Chatbot API",
        "status": "healthy",
        "version": settings.api_version,
        "features": [
            "Session-aware chat endpoints",
            "Vector-based intent matching",
            "Redis session management",
            "ChromaDB vector storage",
            "Structured logging",
            "Health monitoring",
            "Error handling middleware",
        ],
        "endpoints": {
            "chat": "/api/v1/chat",
            "sessions": "/api/v1/session",
            "health": "/api/v1/health",
            "docs": "/docs",
        },
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "alfred-api",
        "version": settings.api_version,
    }


@app.get("/test-dependencies")
async def test_dependencies():
    """Test endpoint to verify all dependencies are working"""
    results = {}

    # Test other dependencies
    try:
        import pydantic

        results["pydantic"] = {"status": "OK", "version": pydantic.VERSION}
    except Exception as e:
        results["pydantic"] = {"status": "ERROR", "error": str(e)}

    return {"dependency_check": results}


if __name__ == "__main__":
    import uvicorn

    print(f"Starting {settings.api_title} v{settings.api_version}")
    print(f"Visit: http://localhost:{settings.api_port}")
    print(f"Docs: http://localhost:{settings.api_port}/docs")

    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level="info",
    )
