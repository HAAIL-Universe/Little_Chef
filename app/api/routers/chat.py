from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.schemas import (
    ChatRequest,
    ChatResponse,
    ConfirmProposalRequest,
    ConfirmProposalResponse,
    ErrorResponse,
    UserMe,
)
from app.services.chat_service import ChatService
from app.services.prefs_service import get_prefs_service
from app.services.proposal_store import ProposalStore

router = APIRouter(prefix="", tags=["Chat"])

# Shared instances (in-memory, process-local)
_proposal_store = ProposalStore()
_chat_service = ChatService(get_prefs_service(), _proposal_store)


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={"401": {"model": ErrorResponse}},
)
def chat(
    request: ChatRequest,
    current_user: UserMe = Depends(get_current_user),
) -> ChatResponse:
    return _chat_service.handle_chat(current_user.user_id, request)


@router.post(
    "/chat/confirm",
    response_model=ConfirmProposalResponse,
    responses={
        "400": {"model": ErrorResponse},
        "401": {"model": ErrorResponse},
    },
)
def chat_confirm(
    request: ConfirmProposalRequest,
    current_user: UserMe = Depends(get_current_user),
) -> ConfirmProposalResponse:
    applied = _chat_service.confirm(current_user.user_id, request.proposal_id, request.confirm)
    if not applied and request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(error="bad_request", message="proposal not found").model_dump(),
        )
    return ConfirmProposalResponse(applied=applied, applied_event_ids=[])

