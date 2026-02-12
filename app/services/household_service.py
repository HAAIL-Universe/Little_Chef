"""Household sync service — Phase 13.3.

Lightweight event notification system for household-level sharing.

Members can join a household (by invite code), and consumption/shopping
events are broadcast to all household members.  In-memory MVP — no
persistence beyond the process lifetime.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class HouseholdMember(BaseModel):
    user_id: str
    display_name: str = ""
    joined_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Household(BaseModel):
    household_id: str
    name: str
    invite_code: str
    owner_id: str
    members: list[HouseholdMember] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HouseholdEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str
    source_user_id: str
    event_type: str  # "consume_cooked", "staple_added", "shopping_updated", "inventory_added"
    summary: str  # Human-readable summary
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class HouseholdCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)


class HouseholdJoinRequest(BaseModel):
    invite_code: str = Field(..., min_length=1)


class HouseholdEventListResponse(BaseModel):
    events: list[HouseholdEvent]


class HouseholdResponse(BaseModel):
    household_id: str
    name: str
    invite_code: str
    members: list[HouseholdMember]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class HouseholdService:
    """In-memory household management and event notification."""

    def __init__(self) -> None:
        self._households: dict[str, Household] = {}       # household_id → Household
        self._user_household: dict[str, str] = {}          # user_id → household_id
        self._events: dict[str, list[HouseholdEvent]] = {} # household_id → events

    def create_household(self, user_id: str, name: str, display_name: str = "") -> Household:
        """Create a new household. The creator becomes the owner and first member."""
        household_id = str(uuid.uuid4())
        invite_code = uuid.uuid4().hex[:8].upper()
        member = HouseholdMember(user_id=user_id, display_name=display_name or user_id)
        household = Household(
            household_id=household_id,
            name=name,
            invite_code=invite_code,
            owner_id=user_id,
            members=[member],
        )
        self._households[household_id] = household
        self._user_household[user_id] = household_id
        self._events[household_id] = []
        return household

    def join_household(self, user_id: str, invite_code: str, display_name: str = "") -> Optional[Household]:
        """Join a household using an invite code. Returns None if code is invalid."""
        for household in self._households.values():
            if household.invite_code == invite_code:
                # Check if already a member
                if any(m.user_id == user_id for m in household.members):
                    return household
                member = HouseholdMember(user_id=user_id, display_name=display_name or user_id)
                household.members.append(member)
                self._user_household[user_id] = household.household_id
                return household
        return None

    def leave_household(self, user_id: str) -> bool:
        """Remove user from their household."""
        household_id = self._user_household.pop(user_id, None)
        if not household_id:
            return False
        household = self._households.get(household_id)
        if household:
            household.members = [m for m in household.members if m.user_id != user_id]
            # If no members left, remove the household
            if not household.members:
                del self._households[household_id]
                self._events.pop(household_id, None)
        return True

    def get_household(self, user_id: str) -> Optional[Household]:
        """Get the household a user belongs to."""
        household_id = self._user_household.get(user_id)
        if not household_id:
            return None
        return self._households.get(household_id)

    def broadcast_event(
        self,
        user_id: str,
        event_type: str,
        summary: str,
    ) -> Optional[HouseholdEvent]:
        """Broadcast an event to all household members.

        Returns the event if the user is in a household, None otherwise.
        """
        household_id = self._user_household.get(user_id)
        if not household_id:
            return None
        event = HouseholdEvent(
            household_id=household_id,
            source_user_id=user_id,
            event_type=event_type,
            summary=summary,
        )
        self._events.setdefault(household_id, []).append(event)
        # Keep only last 100 events per household
        if len(self._events[household_id]) > 100:
            self._events[household_id] = self._events[household_id][-100:]
        return event

    def get_events(self, user_id: str, limit: int = 20) -> list[HouseholdEvent]:
        """Get recent household events for the user's household."""
        household_id = self._user_household.get(user_id)
        if not household_id:
            return []
        events = self._events.get(household_id, [])
        return list(reversed(events[-limit:]))

    def get_member_ids(self, user_id: str) -> list[str]:
        """Get all member user_ids in the user's household (excluding self)."""
        household = self.get_household(user_id)
        if not household:
            return []
        return [m.user_id for m in household.members if m.user_id != user_id]


_household_service: HouseholdService | None = None


def get_household_service() -> HouseholdService:
    global _household_service
    if _household_service is None:
        _household_service = HouseholdService()
    return _household_service


def reset_household_service() -> None:
    global _household_service
    _household_service = None
