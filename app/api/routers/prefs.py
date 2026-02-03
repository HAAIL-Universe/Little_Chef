from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas import UserPrefs, UserPrefsUpsertRequest, ErrorResponse, UserMe
from app.services.prefs_service import get_prefs_service
from app.errors import BadRequestError

router = APIRouter(prefix="", tags=["Prefs"], dependencies=[])


@router.get(
    "/prefs",
    response_model=UserPrefs,
    responses={"401": {"model": ErrorResponse}},
)
def get_prefs(current_user: UserMe = Depends(get_current_user)) -> UserPrefs:
    service = get_prefs_service()
    return service.get_prefs(current_user.user_id)


@router.put(
    "/prefs",
    response_model=UserPrefs,
    responses={
        "400": {"model": ErrorResponse},
        "401": {"model": ErrorResponse},
    },
)
def upsert_prefs(
    request: UserPrefsUpsertRequest,
    current_user: UserMe = Depends(get_current_user),
) -> UserPrefs:
    service = get_prefs_service()
    prefs = request.prefs
    if prefs.servings < 1 or prefs.meals_per_day < 1:
        raise BadRequestError("servings and meals_per_day must be >= 1")
    return service.upsert_prefs(
        current_user.user_id,
        current_user.provider_subject,
        current_user.email,
        prefs,
    )
