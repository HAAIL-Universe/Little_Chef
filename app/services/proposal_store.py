import time
from typing import Dict, Optional

from app.schemas import ProposedUpsertPrefsAction


class ProposalStore:
    """
    Phase 2 in-memory proposal store.
    Uses per-user map of proposal_id -> ProposedUpsertPrefsAction and a simple TTL.
    """

    def __init__(self, ttl_seconds: int = 900) -> None:
        self.ttl_seconds = ttl_seconds
        self._data: Dict[str, Dict[str, tuple[float, ProposedUpsertPrefsAction]]] = {}

    def save(self, user_id: str, proposal_id: str, action: ProposedUpsertPrefsAction) -> None:
        user_bucket = self._data.setdefault(user_id, {})
        user_bucket[proposal_id] = (time.time(), action)
        self._gc(user_bucket)

    def pop(self, user_id: str, proposal_id: str) -> Optional[ProposedUpsertPrefsAction]:
        user_bucket = self._data.get(user_id)
        if not user_bucket:
            return None
        self._gc(user_bucket)
        entry = user_bucket.pop(proposal_id, None)
        if not entry:
            return None
        _, action = entry
        return action

    def peek(self, user_id: str, proposal_id: str) -> Optional[ProposedUpsertPrefsAction]:
        user_bucket = self._data.get(user_id)
        if not user_bucket:
            return None
        self._gc(user_bucket)
        entry = user_bucket.get(proposal_id)
        if not entry:
            return None
        _, action = entry
        return action

    def _gc(self, bucket: Dict[str, tuple[float, ProposedUpsertPrefsAction]]) -> None:
        now = time.time()
        expired = [pid for pid, (created, _) in bucket.items() if now - created > self.ttl_seconds]
        for pid in expired:
            bucket.pop(pid, None)

    def clear(self) -> None:
        self._data.clear()
