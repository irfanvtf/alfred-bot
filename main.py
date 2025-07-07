# main.py - Phase 6: FastAPI Integration Complete
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from config.settings import settings

# Import API routes
from src.api.routes.chat import router as chat_router
from src.api.routes.session import router as session_router
from src.api.routes.health import router as health_router

# Import middleware and error handling
from src.api.middleware import (
    ErrorHandlingMiddleware,
    LoggingMiddleware,
    setup_exception_handlers,
)

# Import logging configuration
from src.utils.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
log_level = os.getenv("LOG_LEVEL", "INFO")
log_to_file = os.getenv("LOG_TO_FILE", "true").lower() == "true"
setup_logging(log_level=log_level, log_to_file=log_to_file)

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
    description="A session-aware knowledge-based chatbot using spaCy and ChromaDB",
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

# Include API routers
app.include_router(chat_router, prefix="/api/v1")
app.include_router(session_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")


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

    # Test spaCy
    try:
        import spacy

        nlp = spacy.load("en_core_web_md")
        doc = nlp("test")
        results["spacy"] = {
            "status": "OK",
            "model": "en_core_web_md",
            "vector_size": len(doc.vector),
        }
    except Exception as e:
        try:
            import spacy

            nlp = spacy.load("en_core_web_sm")
            doc = nlp("test")
            results["spacy"] = {
                "status": "OK",
                "model": "en_core_web_sm",
                "vector_size": len(doc.vector),
                "note": "Using small model - consider upgrading to en_core_web_md",
            }
        except Exception as e2:
            results["spacy"] = {"status": "ERROR", "error": str(e2)}

    # Test Pinecone
    try:
        import pinecone

        api_key = os.getenv("PINECONE_API_KEY")
        if api_key:
            results["pinecone"] = {"status": "OK", "api_key_set": True}
        else:
            results["pinecone"] = {
                "status": "WARNING",
                "api_key_set": False,
                "message": "API key not set",
            }
    except Exception as e:
        results["pinecone"] = {"status": "ERROR", "error": str(e)}

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
