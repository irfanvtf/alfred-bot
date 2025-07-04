from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from src.services.session_manager import session_manager
from src.models.session import SessionCreate, SessionData
from src.utils.session_utils import get_session_summary

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/create", response_model=SessionData)
async def create_session(session_create: SessionCreate):
    """Create a new chat session"""
    try:
        session = session_manager.create_session(session_create)
        return session
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create session: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionData)
async def get_session(session_id: str):
    """Get session by ID"""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    success = session_manager.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted successfully"}


@router.get("/{session_id}/summary")
async def get_session_summary_endpoint(session_id: str):
    """Get session summary"""
    summary = get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    return summary


@router.get("/health/redis")
async def redis_health_check():
    """Check Redis connection health"""
    try:
        session_manager.redis.ping()
        active_sessions = session_manager.get_active_sessions_count()
        return {"status": "healthy", "active_sessions": active_sessions}
    except Exception as e:
        raise HTTPException(
            status_code=503, detail=f"Redis connection failed: {str(e)}"
        )
