from typing import Dict, List, Optional
from uuid import uuid4
from datetime import datetime, timezone

from app.schemas import InventoryEvent, InventoryEventCreateRequest


class InventoryRepository:
    """
    Phase 3 in-memory inventory event store (per user).
    Replace with persistent store in later phase.
    """

    def __init__(self) -> None:
        self._events_by_user: Dict[str, List[InventoryEvent]] = {}

    def create_event(self, user_id: str, req: InventoryEventCreateRequest) -> InventoryEvent:
        occurred_at = req.occurred_at or datetime.now(timezone.utc).isoformat()
        event = InventoryEvent(
            event_id=str(uuid4()),
            occurred_at=occurred_at,
            event_type=req.event_type,
            item_name=req.item_name.strip(),
            quantity=req.quantity,
            unit=req.unit,
            note=req.note or "",
            source=req.source,
        )
        bucket = self._events_by_user.setdefault(user_id, [])
        bucket.append(event)
        return event

    def list_events(self, user_id: str, limit: int = 50, since: Optional[str] = None) -> List[InventoryEvent]:
        bucket = self._events_by_user.get(user_id, [])
        filtered = bucket
        if since:
            filtered = [e for e in bucket if e.occurred_at > since]
        return list(reversed(filtered))[:limit]

    def all_events(self, user_id: str) -> List[InventoryEvent]:
        return list(self._events_by_user.get(user_id, []))

    def clear(self) -> None:
        self._events_by_user.clear()
