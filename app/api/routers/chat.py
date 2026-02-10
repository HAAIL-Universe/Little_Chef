from fastapi import APIRouter, Depends

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
from app.services.inventory_service import get_inventory_service
from app.services.proposal_store import ProposalStore
from app.services.llm_client import get_llm_client
from app.services.thread_messages_repo import ThreadMessagesRepo
from app.errors import BadRequestError

router = APIRouter(prefix="", tags=["Chat"])

# Shared instances (in-memory, process-local)
_proposal_store = ProposalStore()
_thread_messages_repo = ThreadMessagesRepo()
_chat_service = ChatService(
    get_prefs_service(), get_inventory_service(), _proposal_store, get_llm_client(), _thread_messages_repo
)


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={"401": {"model": ErrorResponse}},
)
def chat(
    request: ChatRequest,
    current_user: UserMe = Depends(get_current_user),
) -> ChatResponse:
    return _chat_service.handle_chat(current_user, request)


@router.post(
    "/chat/inventory",
    response_model=ChatResponse,
    responses={
        "400": {"model": ErrorResponse},
        "401": {"model": ErrorResponse},
    },
)
def chat_inventory(
    request: ChatRequest,
    current_user: UserMe = Depends(get_current_user),
) -> ChatResponse:
    if not request.thread_id:
        raise BadRequestError("Thread id is required for inventory flow.")
    if not request.mode or (request.mode or "").lower() != "fill":
        raise BadRequestError("inventory supports fill only in Phase 8 (use mode='fill').")
    return _chat_service.inventory_agent.handle_fill(current_user, request)


@router.post(
    "/chat/mealplan",
    response_model=ChatResponse,
    responses={
        "400": {"model": ErrorResponse},
        "401": {"model": ErrorResponse},
    },
)
def chat_mealplan(
    request: ChatRequest,
    current_user: UserMe = Depends(get_current_user),
) -> ChatResponse:
    if not request.thread_id:
        raise BadRequestError("Thread id is required for meal plan flow.")
    if not request.mode or (request.mode or "").lower() != "fill":
        raise BadRequestError("mealplan supports fill only (use mode='fill').")
    return _chat_service.chef_agent.handle_fill(current_user, request)


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
    applied, applied_event_ids, reason = _chat_service.confirm(
        current_user, request.proposal_id, request.confirm, request.thread_id
    )
    if not applied and request.confirm and reason is None:
        raise BadRequestError("proposal not found")
    return ConfirmProposalResponse(
        applied=applied, applied_event_ids=applied_event_ids, reason=reason
    )


def reset_chat_state_for_tests() -> None:
    """
    Testing helper: clear proposal store and rebuild chat service with fresh prefs service.
    """
    global _chat_service
    _proposal_store.clear()
    get_prefs_service.cache_clear()
    get_inventory_service.cache_clear()
    global _thread_messages_repo
    _thread_messages_repo = ThreadMessagesRepo()
    _chat_service = ChatService(
        get_prefs_service(), get_inventory_service(), _proposal_store, get_llm_client(), _thread_messages_repo
    )
