"""Tests for Phase 13.3 — Household sync concept.

Covers: create, join (invite code), leave, events feed, member listing,
error paths, and OpenAPI schema presence.
"""

import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.schemas import UserMe


# ---------------------------------------------------------------------------
# Multi-user fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def user_client(app_instance, _clear_db_env):
    """Client authenticated as 'test-user'."""
    app_instance.dependency_overrides[get_current_user] = lambda: UserMe(
        user_id="test-user", provider_subject="sub1", email=None
    )
    with TestClient(app_instance) as c:
        yield c
    app_instance.dependency_overrides.pop(get_current_user, None)


def _switch_user(app_instance, user_id: str) -> None:
    """Switch the authed user for subsequent requests."""
    app_instance.dependency_overrides[get_current_user] = lambda: UserMe(
        user_id=user_id, provider_subject=f"sub-{user_id}", email=None
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCreateHousehold:
    def test_create_success(self, user_client, app_instance):
        resp = user_client.post("/household", json={"name": "Test Home"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "Test Home"
        assert body["invite_code"]
        assert len(body["members"]) == 1
        assert body["members"][0]["user_id"] == "test-user"

    def test_create_returns_invite_code(self, user_client, app_instance):
        resp = user_client.post("/household", json={"name": "My Place"})
        code = resp.json()["invite_code"]
        assert len(code) == 8
        assert code == code.upper()

    def test_create_already_in_household(self, user_client, app_instance):
        user_client.post("/household", json={"name": "Home 1"})
        resp = user_client.post("/household", json={"name": "Home 2"})
        assert resp.status_code == 400
        assert "already" in resp.json()["message"].lower()


class TestJoinHousehold:
    def test_join_success(self, user_client, app_instance):
        # Owner creates
        _switch_user(app_instance, "owner")
        resp = user_client.post("/household", json={"name": "Home"})
        code = resp.json()["invite_code"]

        # Joiner joins
        _switch_user(app_instance, "joiner")
        join_resp = user_client.post("/household/join", json={"invite_code": code})
        assert join_resp.status_code == 200
        members = join_resp.json()["members"]
        user_ids = [m["user_id"] for m in members]
        assert "owner" in user_ids
        assert "joiner" in user_ids

    def test_join_invalid_code(self, user_client, app_instance):
        resp = user_client.post("/household/join", json={"invite_code": "BADCODE1"})
        assert resp.status_code == 400
        assert "invalid" in resp.json()["message"].lower()

    def test_join_already_in_household(self, user_client, app_instance):
        # Owner1 creates household 1
        _switch_user(app_instance, "owner1")
        r1 = user_client.post("/household", json={"name": "Home A"})
        code1 = r1.json()["invite_code"]

        # Owner2 creates household 2
        _switch_user(app_instance, "owner2")
        user_client.post("/household", json={"name": "Home B"})

        # Owner2 tries to join household 1
        resp = user_client.post("/household/join", json={"invite_code": code1})
        assert resp.status_code == 400
        assert "already" in resp.json()["message"].lower()


class TestGetHousehold:
    def test_get_success(self, user_client, app_instance):
        user_client.post("/household", json={"name": "Test Home"})
        resp = user_client.get("/household")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test Home"

    def test_get_not_in_household(self, user_client, app_instance):
        resp = user_client.get("/household")
        assert resp.status_code == 404
        assert "not in" in resp.json()["message"].lower()


class TestLeaveHousehold:
    def test_leave_success(self, user_client, app_instance):
        user_client.post("/household", json={"name": "Home"})
        resp = user_client.delete("/household")
        assert resp.status_code == 200
        assert "left" in resp.json()["detail"].lower()
        get_resp = user_client.get("/household")
        assert get_resp.status_code == 404

    def test_leave_not_in_household(self, user_client, app_instance):
        resp = user_client.delete("/household")
        assert resp.status_code == 404

    def test_leave_cleans_up_empty(self, user_client, app_instance):
        """When last member leaves, household should be deleted."""
        user_client.post("/household", json={"name": "Home"})
        user_client.delete("/household")
        resp = user_client.get("/household")
        assert resp.status_code == 404


class TestHouseholdEvents:
    def test_events_empty(self, user_client, app_instance):
        user_client.post("/household", json={"name": "Home"})
        resp = user_client.get("/household/events")
        assert resp.status_code == 200
        assert resp.json()["events"] == []

    def test_events_not_in_household(self, user_client, app_instance):
        resp = user_client.get("/household/events")
        assert resp.status_code == 200
        assert resp.json()["events"] == []

    def test_broadcast_event_visible(self, user_client, app_instance):
        """Broadcast via service layer and verify events endpoint returns it."""
        from app.services.household_service import get_household_service

        user_client.post("/household", json={"name": "Home"})
        svc = get_household_service()
        svc.broadcast_event("test-user", "consume_cooked", "Cooked Pasta")

        resp = user_client.get("/household/events")
        assert resp.status_code == 200
        events = resp.json()["events"]
        assert len(events) == 1
        assert events[0]["event_type"] == "consume_cooked"
        assert "Pasta" in events[0]["summary"]

    def test_broadcast_visible_to_all_members(self, user_client, app_instance):
        """Events broadcast by one member are visible to others."""
        from app.services.household_service import get_household_service

        _switch_user(app_instance, "owner")
        resp = user_client.post("/household", json={"name": "Home"})
        code = resp.json()["invite_code"]

        _switch_user(app_instance, "member2")
        user_client.post("/household/join", json={"invite_code": code})

        svc = get_household_service()
        svc.broadcast_event("owner", "staple_added", "Owner added Rice as staple")

        # member2 should see the event
        resp = user_client.get("/household/events")
        events = resp.json()["events"]
        assert len(events) == 1
        assert events[0]["source_user_id"] == "owner"


class TestHouseholdServiceDirect:
    """Test the service layer directly."""

    def test_member_ids_excludes_self(self, app_instance):
        from app.services.household_service import get_household_service

        svc = get_household_service()
        h = svc.create_household("alice", "Home")
        svc.join_household("bob", h.invite_code)
        assert svc.get_member_ids("alice") == ["bob"]
        assert svc.get_member_ids("bob") == ["alice"]

    def test_event_limit_100(self, app_instance):
        from app.services.household_service import get_household_service

        svc = get_household_service()
        svc.create_household("alice", "Home")
        for i in range(110):
            svc.broadcast_event("alice", "test", f"Event {i}")
        events = svc.get_events("alice", limit=200)
        assert len(events) <= 100

    def test_broadcast_no_household(self, app_instance):
        from app.services.household_service import get_household_service

        svc = get_household_service()
        result = svc.broadcast_event("nobody", "test", "Nothing")
        assert result is None


class TestHouseholdOpenAPI:
    def test_endpoint_in_openapi(self, client, app_instance):
        resp = client.get("/openapi.json")
        spec = resp.json()
        assert "/household" in spec["paths"]
        assert "/household/join" in spec["paths"]
        assert "/household/events" in spec["paths"]
