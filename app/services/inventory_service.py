from functools import lru_cache
from typing import List, Dict, Set, Tuple
from datetime import datetime, timezone

from app.repos.inventory_repo import InventoryRepository, DbInventoryRepository, get_inventory_repository
from app.schemas import (
    InventoryEventCreateRequest,
    InventoryEvent,
    InventorySummaryResponse,
    InventorySummaryItem,
    LowStockResponse,
    LowStockItem,
    StapleItem,
)


THRESHOLDS = {
    "count": 1,
    "g": 100,
    "ml": 100,
}


class InventoryService:
    def __init__(self, repo) -> None:
        self.repo = repo
        # staples: user_id -> set of (normalized_item_name, unit)
        self._staples: Dict[str, Set[Tuple[str, str]]] = {}

    def create_event(self, user_id: str, provider_subject: str, email: str | None, req: InventoryEventCreateRequest) -> InventoryEvent:
        try:
            return self.repo.create_event(user_id, provider_subject, email, req)
        except TypeError:
            # fall back to in-memory signature (user_id, req)
            return self.repo.create_event(user_id, req)

    def list_events(self, user_id: str, limit: int, since: str | None) -> List[InventoryEvent]:
        return self.repo.list_events(user_id, limit=limit, since=since)

    def has_events(self, user_id: str) -> bool:
        try:
            if hasattr(self.repo, "has_events"):
                return bool(self.repo.has_events(user_id))
            return bool(self.repo.all_events(user_id))
        except Exception:
            return False

    def summary(self, user_id: str) -> InventorySummaryResponse:
        aggregates: Dict[tuple[str, str, str], float] = {}
        events = self.repo.all_events(user_id)
        for ev in events:
            unit = ev.unit or "count"
            location = getattr(ev, "location", None) or "pantry"
            qty = ev.quantity if ev.quantity is not None else 0
            key = (self._normalize(ev.item_name), unit, location)
            if ev.event_type == "adjust":
                aggregates[key] = qty
            else:
                delta = qty if ev.event_type == "add" else -qty
                aggregates[key] = aggregates.get(key, 0) + delta

        items: List[InventorySummaryItem] = []
        for (name, unit, location), qty in aggregates.items():
            approx = False
            if qty < 0:
                qty = 0
                approx = True
            items.append(InventorySummaryItem(item_name=name, quantity=qty, unit=unit, location=location, approx=approx))

        generated_at = datetime.now(timezone.utc).isoformat()
        return InventorySummaryResponse(items=items, generated_at=generated_at)

    def low_stock(self, user_id: str) -> LowStockResponse:
        summary = self.summary(user_id)
        lows: List[LowStockItem] = []
        # Track all items that appear in summary (regardless of stock level)
        summary_keys: set[tuple[str, str]] = set()
        user_staples = self._staples.get(user_id, set())

        for item in summary.items:
            threshold = THRESHOLDS.get(item.unit, 0)
            key = (self._normalize(item.item_name), item.unit)
            summary_keys.add(key)
            is_staple = key in user_staples
            if item.quantity <= threshold:
                reason = "staple: low/out of stock" if is_staple else "below threshold"
                lows.append(
                    LowStockItem(
                        item_name=item.item_name,
                        quantity=item.quantity,
                        unit=item.unit,
                        threshold=threshold,
                        reason=reason,
                        is_staple=is_staple,
                    )
                )

        # Staples with zero inventory (never added) should also appear
        for (name, unit) in user_staples:
            if (name, unit) not in summary_keys:
                threshold = THRESHOLDS.get(unit, 0)
                lows.append(
                    LowStockItem(
                        item_name=name,
                        quantity=0,
                        unit=unit,
                        threshold=threshold,
                        reason="staple: out of stock",
                        is_staple=True,
                    )
                )

        return LowStockResponse(items=lows, generated_at=summary.generated_at)

    # ── Staples management ──────────────────────────────────────────────

    def set_staple(self, user_id: str, item_name: str, unit: str = "count") -> bool:
        """Mark an item as a staple. Returns True if newly added."""
        key = (self._normalize(item_name), unit)
        user_set = self._staples.setdefault(user_id, set())
        if key in user_set:
            return False
        user_set.add(key)
        return True

    def remove_staple(self, user_id: str, item_name: str, unit: str = "count") -> bool:
        """Remove staple status. Returns True if it was a staple."""
        key = (self._normalize(item_name), unit)
        user_set = self._staples.get(user_id, set())
        if key not in user_set:
            return False
        user_set.discard(key)
        return True

    def list_staples(self, user_id: str) -> List[StapleItem]:
        """Return all staple items for a user."""
        user_set = self._staples.get(user_id, set())
        return [StapleItem(item_name=name, unit=unit) for name, unit in sorted(user_set)]

    def is_staple(self, user_id: str, item_name: str, unit: str = "count") -> bool:
        key = (self._normalize(item_name), unit)
        return key in self._staples.get(user_id, set())

    def clear(self) -> None:
        self.repo.clear()

    def _normalize(self, name: str) -> str:
        return name.strip().lower()


@lru_cache(maxsize=1)
def get_inventory_service() -> InventoryService:
    repo = get_inventory_repository()
    return InventoryService(repo)
