from functools import lru_cache
from typing import List, Dict
from datetime import datetime, timezone

from app.repos.inventory_repo import InventoryRepository
from app.schemas import (
    InventoryEventCreateRequest,
    InventoryEvent,
    InventorySummaryResponse,
    InventorySummaryItem,
    LowStockResponse,
    LowStockItem,
)


THRESHOLDS = {
    "count": 1,
    "g": 100,
    "ml": 100,
}


class InventoryService:
    def __init__(self, repo: InventoryRepository) -> None:
        self.repo = repo

    def create_event(self, user_id: str, req: InventoryEventCreateRequest) -> InventoryEvent:
        return self.repo.create_event(user_id, req)

    def list_events(self, user_id: str, limit: int, since: str | None) -> List[InventoryEvent]:
        return self.repo.list_events(user_id, limit=limit, since=since)

    def summary(self, user_id: str) -> InventorySummaryResponse:
        aggregates: Dict[tuple[str, str], float] = {}
        events = self.repo.all_events(user_id)
        for ev in events:
            key = (self._normalize(ev.item_name), ev.unit)
            if ev.event_type == "adjust":
                aggregates[key] = ev.quantity
            else:
                delta = ev.quantity if ev.event_type == "add" else -ev.quantity
                aggregates[key] = aggregates.get(key, 0) + delta

        items: List[InventorySummaryItem] = []
        for (name, unit), qty in aggregates.items():
            approx = False
            if qty < 0:
                qty = 0
                approx = True
            items.append(InventorySummaryItem(item_name=name, quantity=qty, unit=unit, approx=approx))

        generated_at = datetime.now(timezone.utc).isoformat()
        return InventorySummaryResponse(items=items, generated_at=generated_at)

    def low_stock(self, user_id: str) -> LowStockResponse:
        summary = self.summary(user_id)
        lows: List[LowStockItem] = []
        for item in summary.items:
            threshold = THRESHOLDS.get(item.unit, 0)
            if item.quantity <= threshold:
                lows.append(
                    LowStockItem(
                        item_name=item.item_name,
                        quantity=item.quantity,
                        unit=item.unit,
                        threshold=threshold,
                        reason="",
                    )
                )
        return LowStockResponse(items=lows, generated_at=summary.generated_at)

    def clear(self) -> None:
        self.repo.clear()

    def _normalize(self, name: str) -> str:
        return name.strip().lower()


@lru_cache(maxsize=1)
def get_inventory_service() -> InventoryService:
    repo = InventoryRepository()
    return InventoryService(repo)
