from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user
from app.schemas import (
    ErrorResponse,
    InventoryEvent,
    InventoryEventCreateRequest,
    InventoryEventListResponse,
    InventorySummaryResponse,
    LowStockResponse,
    StapleToggleRequest,
    StapleToggleResponse,
    StaplesListResponse,
    UserMe,
)
from app.services.inventory_service import get_inventory_service

router = APIRouter(prefix="", tags=["Inventory"])


@router.get(
    "/inventory/events",
    response_model=InventoryEventListResponse,
    responses={"401": {"model": ErrorResponse}},
)
def list_inventory_events(
    limit: int = Query(50, ge=1, le=200),
    since: str | None = Query(None),
    current_user: UserMe = Depends(get_current_user),
) -> InventoryEventListResponse:
    service = get_inventory_service()
    events = service.list_events(current_user.user_id, limit=limit, since=since)
    return InventoryEventListResponse(events=events)


@router.post(
    "/inventory/events",
    status_code=status.HTTP_201_CREATED,
    response_model=InventoryEvent,
    responses={"401": {"model": ErrorResponse}},
)
def create_inventory_event(
    request: InventoryEventCreateRequest,
    current_user: UserMe = Depends(get_current_user),
) -> InventoryEvent:
    service = get_inventory_service()
    return service.create_event(
        current_user.user_id,
        current_user.provider_subject,
        current_user.email,
        request,
    )


@router.get(
    "/inventory/summary",
    response_model=InventorySummaryResponse,
    responses={"401": {"model": ErrorResponse}},
)
def get_inventory_summary(current_user: UserMe = Depends(get_current_user)) -> InventorySummaryResponse:
    service = get_inventory_service()
    return service.summary(current_user.user_id)


@router.get(
    "/inventory/low-stock",
    response_model=LowStockResponse,
    responses={"401": {"model": ErrorResponse}},
)
def get_inventory_low_stock(current_user: UserMe = Depends(get_current_user)) -> LowStockResponse:
    service = get_inventory_service()
    return service.low_stock(current_user.user_id)


@router.get(
    "/inventory/staples",
    response_model=StaplesListResponse,
    responses={"401": {"model": ErrorResponse}},
)
def list_staples(current_user: UserMe = Depends(get_current_user)) -> StaplesListResponse:
    service = get_inventory_service()
    return StaplesListResponse(staples=service.list_staples(current_user.user_id))


@router.post(
    "/inventory/staples",
    response_model=StapleToggleResponse,
    responses={"401": {"model": ErrorResponse}},
)
def set_staple(
    request: StapleToggleRequest,
    current_user: UserMe = Depends(get_current_user),
) -> StapleToggleResponse:
    service = get_inventory_service()
    service.set_staple(current_user.user_id, request.item_name, request.unit)
    return StapleToggleResponse(
        item_name=request.item_name,
        unit=request.unit,
        is_staple=True,
    )


@router.delete(
    "/inventory/staples",
    response_model=StapleToggleResponse,
    responses={"401": {"model": ErrorResponse}},
)
def remove_staple(
    request: StapleToggleRequest,
    current_user: UserMe = Depends(get_current_user),
) -> StapleToggleResponse:
    service = get_inventory_service()
    service.remove_staple(current_user.user_id, request.item_name, request.unit)
    return StapleToggleResponse(
        item_name=request.item_name,
        unit=request.unit,
        is_staple=False,
    )
