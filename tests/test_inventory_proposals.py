from app.services.inventory_agent import InventoryAgent
from app.services.proposal_store import ProposalStore
from app.schemas import UserMe, ChatRequest


class DummyInventoryService:
    def __init__(self):
        self.events = []

    def create_event(self, user_id, provider_subject, email, event):
        class E:
            def __init__(self, eid):
                self.event_id = eid

        eid = f"ev{len(self.events) + 1}"
        self.events.append(event)
        return E(eid)


def make_agent(llm=None):
    inv = DummyInventoryService()
    agent = InventoryAgent(inv, ProposalStore(), llm)
    return agent, inv


def test_pending_edit_updates_without_write(monkeypatch):
    import app.services.inventory_agent as agent_module

    monkeypatch.setattr(
        agent_module,
        "extract_new_draft",
        lambda text, llm: [
            {
                "name_raw": "cereal",
                "quantity_raw": "1",
                "unit_raw": "count",
                "expires_raw": None,
                "notes_raw": None,
            }
        ],
    )
    monkeypatch.setattr(
        agent_module,
        "extract_edit_ops",
        lambda text, llm: {"ops": [{"op": "remove", "target": "cereal"}]},
    )
    monkeypatch.setattr(
        agent_module,
        "normalize_items",
        lambda raw, loc: [
            {
                "item": {
                    "item_key": "cereal",
                    "quantity": 1,
                    "unit": "count",
                    "notes": None,
                    "expires_on": None,
                    "base_name": "cereal",
                },
                "warnings": [],
            }
        ],
    )

    agent, inv = make_agent(llm=None)
    user = UserMe(user_id="u1", provider_subject="s", email=None)

    resp1 = agent.handle_fill(
        user,
        ChatRequest(
            mode="fill",
            message="add cereal",
            include_user_library=True,
            location="pantry",
            thread_id="t1",
        ),
    )
    assert resp1.confirmation_required is True
    resp2 = agent.handle_fill(
        user,
        ChatRequest(
            mode="fill",
            message="remove cereal",
            include_user_library=True,
            location="pantry",
            thread_id="t1",
        ),
    )
    assert resp2.confirmation_required is True
    assert len(inv.events) == 0


def test_deny_clears_pending(monkeypatch):
    import app.services.inventory_agent as agent_module

    monkeypatch.setattr(
        agent_module,
        "extract_new_draft",
        lambda text, llm: [
            {
                "name_raw": "cereal",
                "quantity_raw": "1",
                "unit_raw": "count",
                "expires_raw": None,
                "notes_raw": None,
            }
        ],
    )
    monkeypatch.setattr(
        agent_module,
        "normalize_items",
        lambda raw, loc: [
            {
                "item": {
                    "item_key": "cereal",
                    "quantity": 1,
                    "unit": "count",
                    "notes": None,
                    "expires_on": None,
                    "base_name": "cereal",
                },
                "warnings": [],
            }
        ],
    )

    agent, inv = make_agent(llm=None)
    user = UserMe(user_id="u1", provider_subject="s", email=None)

    resp1 = agent.handle_fill(
        user,
        ChatRequest(
            mode="fill",
            message="add cereal",
            include_user_library=True,
            location="pantry",
            thread_id="t1",
        ),
    )
    pid = resp1.proposal_id
    applied, _, _ = agent.confirm(user, pid, confirm=False, thread_id="t1")
    assert applied is False
    resp2 = agent.handle_fill(
        user,
        ChatRequest(
            mode="fill",
            message="remove cereal",
            include_user_library=True,
            location="pantry",
            thread_id="t1",
        ),
    )
    assert resp2.confirmation_required is True
    assert len(inv.events) == 0


def test_confirm_writes_events(monkeypatch):
    import app.services.inventory_agent as agent_module

    monkeypatch.setattr(
        agent_module,
        "extract_new_draft",
        lambda text, llm: [
            {
                "name_raw": "cereal",
                "quantity_raw": "2",
                "unit_raw": "count",
                "expires_raw": None,
                "notes_raw": None,
            },
            {
                "name_raw": "flour",
                "quantity_raw": "1",
                "unit_raw": "kg",
                "expires_raw": None,
                "notes_raw": None,
            },
        ],
    )
    monkeypatch.setattr(
        agent_module,
        "normalize_items",
        lambda raw, loc: [
            {
                "item": {
                    "item_key": "cereal",
                    "quantity": 2,
                    "unit": "count",
                    "notes": None,
                    "expires_on": None,
                    "base_name": "cereal",
                },
                "warnings": [],
            },
            {
                "item": {
                    "item_key": "flour",
                    "quantity": 1000,
                    "unit": "g",
                    "notes": None,
                    "expires_on": None,
                    "base_name": "flour",
                },
                "warnings": [],
            },
        ],
    )

    agent, inv = make_agent(llm=None)
    user = UserMe(user_id="u1", provider_subject="s", email=None)

    resp1 = agent.handle_fill(
        user,
        ChatRequest(
            mode="fill",
            message="add cereal",
            include_user_library=True,
            location="pantry",
            thread_id="t1",
        ),
    )
    pid = resp1.proposal_id
    assert pid
    assert "u1" in agent.proposal_store._data
    assert pid in agent.proposal_store._data["u1"]
    applied, evs, _ = agent.confirm(user, pid, confirm=True, thread_id="t1")
    assert applied is True
    assert len(inv.events) == 2
    resp2 = agent.handle_fill(
        user,
        ChatRequest(
            mode="fill",
            message="more flour",
            include_user_library=True,
            location="pantry",
            thread_id="t1",
        ),
    )
    assert resp2.confirmation_required is True
