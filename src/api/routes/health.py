# src/api/route/health.py
from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
from src.services.session_manager import session_manager
from src.services.chatbot_engine import chatbot_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """
    General application health check

    Returns:
        Dict containing overall application health status
    """
    try:
        health_status = {
            "status": "healthy",
            "service": "alfred-chatbot",
            "version": "1.0.0",
            "timestamp": None,
        }

        # Add timestamp
        from datetime import datetime

        health_status["timestamp"] = datetime.now().isoformat()

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503, detail=f"Health check failed: {str(e)}"
        ) from e


@router.get("/redis")
async def redis_health_check():
    """
    Check Redis connection and session manager health

    Returns:
        Dict containing Redis health status and session statistics
    """
    try:
        # Test Redis connection
        session_manager.redis.ping()

        # Get session statistics
        active_sessions = session_manager.get_active_session_count()

        # Get Redis info
        redis_info = session_manager.redis.info()
        memory_usage = redis_info.get("used_memory_human", "unknown")

        return {
            "status": "healthy",
            "service": "redis",
            "active_sessions": active_sessions,
            "memory_usage": memory_usage,
            "connected_clients": redis_info.get("connected_clients", "unknown"),
            "uptime_seconds": redis_info.get("uptime_in_seconds", "unknown"),
        }

    except Exception as e:
        logger.error(f"Redis health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503, detail=f"Redis connection failed: {str(e)}"
        )


@router.get("/chroma")
async def chroma_health_check():
    """
    Check ChromaDB vector store health

    Returns:
        Dict containing ChromaDB health status and statistics
    """
    try:
        # Get vector service stats
        vector_stats = chatbot_engine.vector_service.get_stats()

        # Test basic functionality
        test_query = "health check test"
        chatbot_engine.vector_service.search_intents(test_query, {}, top_k=1)

        return {
            "status": "healthy",
            "service": "chroma",
            "collection_stats": vector_stats,
            "test_query_successful": True,
        }

    except Exception as e:
        logger.error(f"Chroma health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=503, detail=f"ChromaDB connection failed: {str(e)}"
        )


@router.get("/dependencies")
async def dependencies_health_check():
    """
    Check all dependencies health

    Returns:
        Dict containing health status of all system dependencies
    """
    health_results = {}
    overall_healthy = True

    # Check Redis
    try:
        session_manager.redis.ping()
        health_results["redis"] = {"status": "healthy", "error": None}
    except Exception as e:
        health_results["redis"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    # Check ChromaDB
    try:
        vector_stats = chatbot_engine.vector_service.get_stats()
        health_results["chroma"] = {
            "status": "healthy",
            "error": None,
            "stats": vector_stats,
        }
    except Exception as e:
        health_results["chroma"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    # Check spaCy
    try:
        nlp = (
            chatbot_engine.vector_service.nlp
            if hasattr(chatbot_engine.vector_service, "nlp")
            else None
        )
        if nlp:
            # Test spaCy processing
            doc = nlp("health check test")
            health_results["spacy"] = {
                "status": "healthy",
                "error": None,
                "model": nlp.meta.get("name", "unknown"),
                "vector_size": len(doc.vector) if doc.has_vector else 0,
            }
        else:
            health_results["spacy"] = {
                "status": "unknown",
                "error": "NLP model not accessible",
            }
    except Exception as e:
        health_results["spacy"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    # Check knowledge base
    try:
        kb_stats = chatbot_engine.knowledge_manager.get_stats()
        health_results["knowledge_base"] = {
            "status": "healthy",
            "error": None,
            "stats": kb_stats,
        }
    except Exception as e:
        health_results["knowledge_base"] = {"status": "unhealthy", "error": str(e)}
        overall_healthy = False

    response = {
        "overall_status": "healthy" if overall_healthy else "unhealthy",
        "dependencies": health_results,
        "timestamp": None,
    }

    # Add timestamp
    from datetime import datetime

    response["timestamp"] = datetime.now().isoformat()

    if not overall_healthy:
        raise HTTPException(status_code=503, detail=response)

    return response


@router.get("/stats")
async def system_stats():
    """
    Get comprehensive system statistics

    Returns:
        Dict containing detailed system performance and usage statistics
    """
    try:
        stats = {
            "chatbot_engine": chatbot_engine.get_engine_stats(),
            "session_manager": {
                "active_sessions": session_manager.get_active_session_count(),
            },
            "timestamp": None,
        }

        # Add Redis stats if available
        try:
            redis_info = session_manager.redis.info()
            stats["redis"] = {
                "memory_usage": redis_info.get("used_memory_human"),
                "connected_clients": redis_info.get("connected_clients"),
                "total_connections": redis_info.get("total_connections_received"),
                "keyspace_hits": redis_info.get("keyspace_hits"),
                "keyspace_misses": redis_info.get("keyspace_misses"),
            }
        except Exception as e:
            stats["redis"] = {"error": str(e)}

        # Add timestamp
        from datetime import datetime

        stats["timestamp"] = datetime.now().isoformat()

        return stats

    except Exception as e:
        logger.error(f"Error getting system stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get system statistics: {str(e)}"
        )
