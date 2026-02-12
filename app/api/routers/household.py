"""Household sync endpoints — Phase 13.3.

Create/join/leave households and view shared event feeds.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.errors import BadRequestError, NotFoundError
from app.schemas import ErrorResponse, UserMe
from app.services.household_service import (
    HouseholdCreateRequest,
    HouseholdEventListResponse,
    HouseholdJoinRequest,
    HouseholdResponse,
    get_household_service,
    reset_household_service,
)


def reset_household_for_tests() -> None:
    """Reset cached household service for test isolation."""
    reset_household_service()

router = APIRouter(prefix="/household", tags=["Household"])


@router.post(
    "",
    response_model=HouseholdResponse,
    responses={"400": {"model": ErrorResponse}, "401": {"model": ErrorResponse}},
)
def create_household(
    request: HouseholdCreateRequest,
    current_user: UserMe = Depends(get_current_user),
) -> HouseholdResponse:
    service = get_household_service()
    existing = service.get_household(current_user.user_id)
    if existing:
        raise BadRequestError("You are already in a household. Leave it first.")
    h = service.create_household(current_user.user_id, request.name)
    return HouseholdResponse(
        household_id=h.household_id,
        name=h.name,
        invite_code=h.invite_code,
        members=h.members,
    )


@router.get(
    "",
    response_model=HouseholdResponse,
    responses={"401": {"model": ErrorResponse}, "404": {"model": ErrorResponse}},
)
def get_household(
    current_user: UserMe = Depends(get_current_user),
) -> HouseholdResponse:
    service = get_household_service()
    h = service.get_household(current_user.user_id)
    if not h:
        raise NotFoundError("You are not in a household.")
    return HouseholdResponse(
        household_id=h.household_id,
        name=h.name,
        invite_code=h.invite_code,
        members=h.members,
    )


@router.post(
    "/join",
    response_model=HouseholdResponse,
    responses={"400": {"model": ErrorResponse}, "401": {"model": ErrorResponse}},
)
def join_household(
    request: HouseholdJoinRequest,
    current_user: UserMe = Depends(get_current_user),
) -> HouseholdResponse:
    service = get_household_service()
    existing = service.get_household(current_user.user_id)
    if existing:
        raise BadRequestError("You are already in a household. Leave it first.")
    h = service.join_household(current_user.user_id, request.invite_code)
    if not h:
        raise BadRequestError("Invalid invite code.")
    return HouseholdResponse(
        household_id=h.household_id,
        name=h.name,
        invite_code=h.invite_code,
        members=h.members,
    )


@router.delete(
    "",
    responses={"401": {"model": ErrorResponse}, "404": {"model": ErrorResponse}},
)
def leave_household(
    current_user: UserMe = Depends(get_current_user),
) -> dict:
    service = get_household_service()
    if not service.leave_household(current_user.user_id):
        raise NotFoundError("You are not in a household.")
    return {"detail": "Left household."}


@router.get(
    "/events",
    response_model=HouseholdEventListResponse,
    responses={"401": {"model": ErrorResponse}},
)
def get_household_events(
    current_user: UserMe = Depends(get_current_user),
) -> HouseholdEventListResponse:
    service = get_household_service()
    events = service.get_events(current_user.user_id)
    return HouseholdEventListResponse(events=events)
