"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request schema."""

    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    session_id: str | None = Field(None, description="Session ID for conversation continuity")
    user_id: str | None = Field(None, description="User/family member ID")


class ChatResponse(BaseModel):
    """Chat response schema."""

    message: str = Field(..., description="Agent response")
    agent: str = Field(..., description="Agent that handled the request")
    session_id: str = Field(..., description="Session ID")
    route: str = Field(..., description="Classified intent route")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "ok"
    version: str = "0.1.0"
