# src/models/schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime


class IntentMetadata(BaseModel):
    """Metadata for an intent"""

    category: str = Field(..., description="Category of the intent")
    confidence_threshold: float = Field(
        0.7, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )
    priority: int = Field(
        1, ge=1, le=10, description="Priority level (1=highest, 10=lowest)"
    )
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class Intent(BaseModel):
    """Single intent with patterns and responses"""

    id: str = Field(..., description="Unique identifier for the intent")
    patterns: List[str] = Field(
        ..., min_items=1, description="List of input patterns that match this intent"
    )
    responses: List[str] = Field(
        ..., min_items=1, description="List of possible responses"
    )
    metadata: IntentMetadata = Field(..., description="Intent metadata")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        if not v.strip():
            raise ValueError("Intent ID cannot be empty")
        # Replace spaces with underscores, convert to lowercase
        return v.strip().lower().replace(" ", "_")

    @field_validator("patterns")
    @classmethod
    def validate_patterns(cls, v):
        # Remove empty patterns and strip whitespace
        patterns = [p.strip() for p in v if p.strip()]
        if not patterns:
            raise ValueError("At least one non-empty pattern is required")
        return patterns

    @field_validator("responses")
    @classmethod
    def validate_responses(cls, v):
        # Remove empty responses and strip whitespace
        responses = [r.strip() for r in v if r.strip()]
        if not responses:
            raise ValueError("At least one non-empty response is required")
        return responses


class KnowledgeBase(BaseModel):
    """Complete knowledge base structure"""

    intents: List[Intent] = Field(..., description="List of all intents")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Knowledge base metadata"
    )
    version: str = Field("1.0.0", description="Knowledge base version")

    @field_validator("intents")
    @classmethod
    def validate_unique_ids(cls, v):
        ids = [intent.id for intent in v]
        if len(ids) != len(set(ids)):
            raise ValueError("All intent IDs must be unique")
        return v


# API Request/Response Models
class ChatRequest(BaseModel):
    """Chat request from user"""

    message: str = Field(..., min_length=1, description="User message")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context"
    )


class ChatResponse(BaseModel):
    """Chat response to user"""

    response: str = Field(..., description="Bot response")
    intent_id: Optional[str] = Field(None, description="Matched intent ID")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional response metadata"
    )


class IntentMatch(BaseModel):
    """Intent matching result"""

    intent_id: str
    confidence: float
    matched_pattern: str
    response: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
