from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.schemas import ErrorResponse, MealPlanGenerateRequest, MealPlanResponse, UserMe
from app.services.mealplan_service import get_mealplan_service

router = APIRouter(prefix="", tags=["MealPlan"])


@router.post(
    "/mealplan/generate",
    response_model=MealPlanResponse,
    responses={"401": {"model": ErrorResponse}},
)
def generate_plan(request: MealPlanGenerateRequest, current_user: UserMe = Depends(get_current_user)) -> MealPlanResponse:
    service = get_mealplan_service()
    return service.generate(request)
