from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Literal


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


class UserPrefs(BaseModel):
    allergies: List[str] = Field(default_factory=list)
    dislikes: List[str] = Field(default_factory=list)
    cuisine_likes: List[str] = Field(default_factory=list)
    servings: int
    meals_per_day: int
    notes: str = ""


class UserPrefsUpsertRequest(BaseModel):
    prefs: UserPrefs


class ProposedUpsertPrefsAction(BaseModel):
    action_type: Literal["upsert_prefs"] = "upsert_prefs"
    prefs: UserPrefs


class ChatRequest(BaseModel):
    mode: Literal["ask", "fill"]
    message: str = Field(..., min_length=1)
    include_user_library: bool = True


class ChatResponse(BaseModel):
    reply_text: str
    confirmation_required: bool
    proposal_id: Optional[str] = None
    proposed_actions: List[ProposedUpsertPrefsAction] = Field(default_factory=list)
    suggested_next_questions: List[str] = Field(default_factory=list)


class ConfirmProposalRequest(BaseModel):
    proposal_id: str
    confirm: bool


class ConfirmProposalResponse(BaseModel):
    applied: bool
    applied_event_ids: List[str] = Field(default_factory=list)
