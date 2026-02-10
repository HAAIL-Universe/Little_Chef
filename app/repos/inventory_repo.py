from typing import Dict, List, Optional
from uuid import uuid4
from datetime import datetime, timezone
import json

from app.schemas import InventoryEvent, InventoryEventCreateRequest
from app.db.conn import get_database_url, connect
from app.repos.user_repo import ensure_user


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
            location=req.location or "pantry",
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

    def has_events(self, user_id: str) -> bool:
        return bool(self._events_by_user.get(user_id))

    def clear(self) -> None:
        self._events_by_user.clear()


class DbInventoryRepository:
    def create_event(self, user_id: str, provider_subject: str, email: str | None, req: InventoryEventCreateRequest) -> InventoryEvent:
        occurred_at = req.occurred_at or datetime.now(timezone.utc).isoformat()
        event_id = str(uuid4())
        payload = {
            "event_type": req.event_type,
            "item_name": req.item_name.strip(),
            "quantity": req.quantity,
            "unit": req.unit,
            "location": req.location or "pantry",
            "note": req.note or "",
            "source": req.source,
        }
        with connect() as conn, conn.cursor() as cur:
            ensure_user(cur, user_id, provider_subject, email)
            cur.execute(
                """
                INSERT INTO inventory_events (event_id, user_id, occurred_at, event_type, payload)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (event_id, user_id, occurred_at, req.event_type, json.dumps(payload)),
            )
            conn.commit()
        return InventoryEvent(event_id=event_id, occurred_at=occurred_at, **payload)

    def list_events(self, user_id: str, limit: int = 50, since: Optional[str] = None) -> List[InventoryEvent]:
        with connect() as conn, conn.cursor() as cur:
            if since:
                cur.execute(
                    """
                    SELECT event_id, occurred_at, payload
                    FROM inventory_events
                    WHERE user_id = %s AND occurred_at > %s
                    ORDER BY occurred_at DESC
                    LIMIT %s
                    """,
                    (user_id, since, limit),
                )
            else:
                cur.execute(
                    """
                    SELECT event_id, occurred_at, payload
                    FROM inventory_events
                    WHERE user_id = %s
                    ORDER BY occurred_at DESC
                    LIMIT %s
                    """,
                    (user_id, limit),
                )
            rows = cur.fetchall()
        events: List[InventoryEvent] = []
        for event_id, occurred_at, payload in rows:
            data = payload
            events.append(
                InventoryEvent(
                    event_id=str(event_id),
                    occurred_at=occurred_at if isinstance(occurred_at, str) else occurred_at.isoformat(),
                    event_type=data["event_type"],
                    item_name=data["item_name"],
                    quantity=data["quantity"],
                    unit=data["unit"],
                    location=data.get("location", "pantry"),
                    note=data.get("note"),
                    source=data.get("source"),
                )
            )
        return events

    def all_events(self, user_id: str) -> List[InventoryEvent]:
        # reuse list_events without since, large limit
        return self.list_events(user_id, limit=1000)

    def has_events(self, user_id: str) -> bool:
        with connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM inventory_events WHERE user_id = %s LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
        return row is not None


def get_inventory_repository():
    if get_database_url():
        return DbInventoryRepository()
    return InventoryRepository()
