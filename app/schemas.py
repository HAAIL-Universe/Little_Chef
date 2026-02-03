from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-friendly message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional extra error metadata")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Health status indicator", pattern="^ok$")


class UserMe(BaseModel):
    user_id: str
    provider_subject: Optional[str] = None
    email: Optional[str] = None

