from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas import ErrorResponse, ShoppingDiffRequest, ShoppingDiffResponse, UserMe
from app.services.shopping_service import get_shopping_service

router = APIRouter(prefix="", tags=["Shopping"])


@router.post(
    "/shopping/diff",
    response_model=ShoppingDiffResponse,
    responses={"401": {"model": ErrorResponse}},
)
def shopping_diff(
    request: ShoppingDiffRequest, current_user: UserMe = Depends(get_current_user)
) -> ShoppingDiffResponse:
    service = get_shopping_service()
    return service.diff(current_user.user_id, request.plan)
