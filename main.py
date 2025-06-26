# main.py - Simplified version for Phase 1
from fastapi import FastAPI
import os
from dotenv import load_dotenv
from config.settings import settings

# Load environment variables
load_dotenv()

# Get configuration from environment variables
API_TITLE = os.getenv("API_TITLE", "Knowledge-Based Chatbot")
API_VERSION = os.getenv("API_VERSION", "1.0.0")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="A knowledge-based chatbot using spaCy and Pinecone",
)


@app.get("/")
async def root():
    return {
        "message": "Alfred Chatbot",
        "status": "Phase 1 - Basic Setup Complete",
        "version": settings.api_version,
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
