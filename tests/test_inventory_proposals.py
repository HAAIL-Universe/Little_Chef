import pytest
from app.services.chat_service import ChatService
from app.services.proposal_store import ProposalStore
from app.services.prefs_service import get_prefs_service
from app.services.inventory_service import get_inventory_service
from app.services.llm_client import LlmClient
from app.schemas import UserMe, ChatRequest


class DummyInventoryService:
    def __init__(self):
        self.events = []

    def create_event(self, user_id, provider_subject, email, event):
        class E:
            def __init__(self, eid):
                self.event_id = eid
        eid = f"ev{len(self.events)+1}"
        self.events.append(event)
        return E(eid)


def make_service(monkeypatch, llm=None):
    inv = DummyInventoryService()
    svc = ChatService(get_prefs_service(), inv, ProposalStore(), llm)
    return svc, inv


def test_pending_edit_updates_without_write(monkeypatch):
    import app.services.chat_service as chat_service

    monkeypatch.setattr(chat_service, "extract_new_draft", lambda text, llm: [{"name_raw": "cereal", "quantity_raw": "1", "unit_raw": "count", "expires_raw": None, "notes_raw": None}])
    monkeypatch.setattr(chat_service, "extract_edit_ops", lambda text, llm: {"ops": [{"op": "remove", "target": "cereal"}]})
    monkeypatch.setattr(chat_service, "normalize_items", lambda raw, loc: [])

    svc, inv = make_service(monkeypatch, llm=None)
    user = UserMe(user_id="u1", provider_subject="s", email=None)

    resp1 = svc.handle_chat(
        user, ChatRequest(mode="fill", message="add cereal", include_user_library=True, location="pantry", thread_id="t1")
    )
    assert resp1.confirmation_required is True
    resp2 = svc.handle_chat(
        user, ChatRequest(mode="fill", message="remove cereal", include_user_library=True, location="pantry", thread_id="t1")
    )
    assert resp2.confirmation_required is True
    assert len(inv.events) == 0


def test_deny_clears_pending(monkeypatch):
    import app.services.chat_service as chat_service

    monkeypatch.setattr(chat_service, "extract_new_draft", lambda text, llm: [{"name_raw": "cereal", "quantity_raw": "1", "unit_raw": "count", "expires_raw": None, "notes_raw": None}])
    monkeypatch.setattr(chat_service, "normalize_items", lambda raw, loc: [])

    svc, inv = make_service(monkeypatch, llm=None)
    user = UserMe(user_id="u1", provider_subject="s", email=None)

    resp1 = svc.handle_chat(
        user, ChatRequest(mode="fill", message="add cereal", include_user_library=True, location="pantry", thread_id="t1")
    )
    pid = resp1.proposal_id
    applied, evs = svc.confirm(user, pid, confirm=False)
    assert applied is False
    resp2 = svc.handle_chat(
        user, ChatRequest(mode="fill", message="remove cereal", include_user_library=True, location="pantry", thread_id="t1")
    )
    assert resp2.confirmation_required is True


def test_confirm_writes_events(monkeypatch):
    import app.services.chat_service as chat_service

    monkeypatch.setattr(chat_service, "extract_new_draft", lambda text, llm: [{"name_raw": "cereal", "quantity_raw": "2", "unit_raw": "count", "expires_raw": None, "notes_raw": None}, {"name_raw": "flour", "quantity_raw": "1", "unit_raw": "kg", "expires_raw": None, "notes_raw": None}])
    monkeypatch.setattr(chat_service, "normalize_items", lambda raw, loc: [
        {"item": {"item_key": "cereal", "quantity": 2, "unit": "count", "notes": None, "expires_on": None, "base_name": "cereal"}, "warnings": []},
        {"item": {"item_key": "flour", "quantity": 1000, "unit": "g", "notes": None, "expires_on": None, "base_name": "flour"}, "warnings": []},
    ])

    svc, inv = make_service(monkeypatch, llm=None)
    user = UserMe(user_id="u1", provider_subject="s", email=None)

    resp1 = svc.handle_chat(
        user, ChatRequest(mode="fill", message="add cereal", include_user_library=True, location="pantry", thread_id="t1")
    )
    pid = resp1.proposal_id
    assert pid
    assert "u1" in svc.proposal_store._data
    assert pid in svc.proposal_store._data["u1"]
    applied, evs = svc.confirm(user, pid, confirm=True)
    assert applied is True
    assert len(inv.events) == 2
    resp2 = svc.handle_chat(
        user, ChatRequest(mode="fill", message="more flour", include_user_library=True, location="pantry", thread_id="t1")
    )
    assert resp2.confirmation_required is True
