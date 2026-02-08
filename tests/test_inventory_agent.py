import re

from app.services.inventory_agent import InventoryAgent
from app.services.proposal_store import ProposalStore

STT_INVENTORY_MESSAGE = (
    "I've just been through the cupboard and fridge. Added three onions, two tins of chopped tomatoes, "
    "and one bag of basmati rice about 1 kilo. I've got 10 eggs in the fridge, a 500g pack of pasta, "
    "2 loaves of bread, and six yoghurts. Also 1 bottle of olive oil, about 750ml, and 2 litres of milk. "
    "There's 250g cheddar and 200g ham. I've got four cans of tuna and one jar of peanut butter. "
    "Use by the 10th on the milk and the 12th on the ham. Also got bananas and garlic, no idea how many, "
    "and a bag of frozen peas."
)

STT_CHICKEN_USE_BY = "Two chicken thighs about 1.2 kilos total. Use by the 9th on the chicken thighs."
STT_MILK_BREAD = "Two loaves of bread. Milk 2 litres use by the 11th on the milk."


STT_CUPBOARD_FRIDGE_LONG = (
    "I'm at the cupboard now. I've got pasta 500 grams, basmati rice about 1 kilo total, four tins of chopped tomatoes, "
    "three tins of tuna, one jar of peanut butter, one bottle of olive oil about 500 ml, and a box of cereal. Not sure "
    "how much flour is left, maybe half a bag, and I've got frozen peas in the freezer about 900 grams total. Now I'm "
    "at the fridge. Two packs of chicken thighs, about 1.2 kilos total, use by the 9th, six eggs, two loaves of bread, milk "
    "2 litres use by the 11th, and orange juice 1 litre. That's everything, cheers, ignore that last bit."
)

STT_CONTAINER_SCAN = (
    "Tinned chopped tomatoes, six tins best before February 2027. Greek yoghurt, two pots. "
    "Chicken breast, two pieces. Garlic, one bulb. Milk, two litres, about half left. Cheddar, best before 5 March."
)



def _inventory_events(client):
    resp = client.get("/inventory/events")
    assert resp.status_code == 200
    return resp.json()["events"]


class _DummyInventoryService:
    def __init__(self):
        self.events = []

    def create_event(self, user_id, provider_subject, email, event):
        class E:
            def __init__(self, eid):
                self.event_id = eid

        eid = f"ev{len(self.events) + 1}"
        self.events.append(event)
        return E(eid)


def _make_agent():
    inv = _DummyInventoryService()
    agent = InventoryAgent(inv, ProposalStore())
    return agent, inv


def test_inventory_agent_allowlist_and_isolation(authed_client):
    thread = "inv-allowlist"
    resp = authed_client.post(
        "/chat/inventory",
        json={"mode": "fill", "message": "added 3 tomatoes", "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    actions = body["proposed_actions"]
    assert actions
    assert all(action["action_type"] == "create_inventory_event" for action in actions)
    assert not any(action["action_type"] == "upsert_prefs" for action in actions)
    assert all(action["event"]["event_type"] == "add" for action in actions)


def test_inventory_fallback_parses_multiple_items(authed_client):
    thread = "inv-fallback-list"
    resp = authed_client.post(
        "/chat/inventory",
        json={
            "mode": "fill",
            "message": "cheddar 300 grams, milk 2 litres, eggs 6",
            "thread_id": thread,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    actions = body["proposed_actions"]
    assert len(actions) >= 3
    assert all(action["action_type"] == "create_inventory_event" for action in actions)
    assert all(action["event"]["event_type"] == "add" for action in actions)
    assert any(
        action["event"]["quantity"] == 300 and action["event"]["unit"] == "g"
        for action in actions
    )
    assert all(len(action["event"]["item_name"]) < 80 for action in actions)


def test_inventory_agent_mode_rejects_non_fill(authed_client):
    resp = authed_client.post(
        "/chat/inventory",
        json={"mode": "ask", "message": "what do I have", "thread_id": "inv-mode"},
    )
    assert resp.status_code == 400
    assert resp.json()["message"] == "inventory supports fill only in Phase 8 (use mode='fill')."


def test_inventory_agent_parse_coerces_event_type():
    agent, _ = _make_agent()
    action, warnings = agent._parse_inventory_action("used 2 apples")
    assert action is not None
    assert action.event.event_type == "add"
    assert "Note: treated as add in Phase 8." in warnings


def test_inventory_agent_parses_stt_inventory_message():
    agent, _ = _make_agent()
    actions, _ = agent._parse_inventory_actions(STT_INVENTORY_MESSAGE)
    assert actions, "Expected actions from the STT inventory message."

    rice_actions = [
        action for action in actions if "basmati rice" in action.event.item_name.lower()
    ]
    assert len(rice_actions) == 1
    assert "egg" not in rice_actions[0].event.item_name.lower()
    assert "weight_g=1000" in (rice_actions[0].event.note or "")

    egg_actions = [
        action for action in actions if "egg" in action.event.item_name.lower()
    ]
    assert len(egg_actions) == 1
    assert egg_actions[0].event.quantity == 10
    assert "rice" not in egg_actions[0].event.item_name.lower()

    bread_actions = [
        action for action in actions if "bread" in action.event.item_name.lower()
    ]
    assert any(
        action.event.quantity == 2 and action.event.unit == "count"
        for action in bread_actions
    )

    milk_actions = [
        action for action in actions if "milk" in action.event.item_name.lower()
    ]
    assert len(milk_actions) == 1
    milk_event = milk_actions[0].event
    assert milk_event.unit == "ml"
    assert milk_event.quantity == 2000.0
    assert "use_by=10th" in (milk_event.note or "")

    olive_actions = [
        action for action in actions if "olive oil" in action.event.item_name.lower()
    ]
    assert len(olive_actions) == 1
    olive_event = olive_actions[0].event
    assert olive_event.quantity == 1
    assert olive_event.unit == "count"
    assert "volume_ml=750" in (olive_event.note or "")

    fillers = [
        "i've just been through the cupboard",
        "no idea how many",
    ]
    for filler in fillers:
        assert not any(
            filler in action.event.item_name.lower() for action in actions
        )

    assert not any(
        action.event.item_name.strip().lower() == "about" for action in actions
    )

    ham_actions = [
        action for action in actions if "ham" in action.event.item_name.lower()
    ]
    assert len(ham_actions) == 1
    assert "use_by=12th" in (ham_actions[0].event.note or "")


def test_inventory_agent_prefers_food_names_over_containers():
    agent, _ = _make_agent()
    actions, _ = agent._parse_inventory_actions(STT_CONTAINER_SCAN)
    assert actions, "Expected actions from the container scan."

    container_words = {
        "tin",
        "tins",
        "can",
        "cans",
        "jar",
        "bottle",
        "bag",
        "pack",
        "box",
        "pot",
        "pots",
        "piece",
        "pieces",
        "bulb",
        "loaf",
        "slice",
        "slices",
    }

    for action in actions:
        name = action.event.item_name.lower()
        assert name not in container_words
        assert "best before" not in name
        assert not re.search(r"\\b(march|february)\\b", name)

    assert any("tomato" in action.event.item_name.lower() for action in actions)
    assert any("yoghurt" in action.event.item_name.lower() for action in actions)
    assert any("chicken" in action.event.item_name.lower() for action in actions)

    expected_foods = {
        "tomato": False,
        "yoghurt": False,
        "chicken": False,
        "garlic": False,
        "milk": False,
        "cheddar": False,
    }
    for action in actions:
        lower_name = action.event.item_name.lower()
        for food in expected_foods:
            if food in lower_name:
                expected_foods[food] = True
    assert all(expected_foods.values())

    date_terms = {"best before", "use by", "use-by", "february", "march"}
    for action in actions:
        lower_name = action.event.item_name.lower()
        assert not any(term in lower_name for term in date_terms)

    milk_actions = [
        action for action in actions if "milk" in action.event.item_name.lower()
    ]
    assert milk_actions
    assert any(
        action.event.quantity == 2000 and action.event.unit == "ml"
        for action in milk_actions
    )

    garlic_actions = [
        action for action in actions if "garlic" in action.event.item_name.lower()
    ]
    assert garlic_actions
    assert garlic_actions[0].event.quantity == 1
    assert garlic_actions[0].event.unit == "count"

    cheddar = next(
        (action for action in actions if "cheddar" in action.event.item_name.lower()),
        None,
    )
    assert cheddar
    cheddar_name = cheddar.event.item_name.lower()
    assert "march" not in cheddar_name
    assert "best before" not in cheddar_name


def test_inventory_agent_handles_chicken_use_by_stt():
    agent, _ = _make_agent()
    actions, _ = agent._parse_inventory_actions(STT_CHICKEN_USE_BY)
    assert actions

    chicken = [
        action for action in actions if "chicken thighs" in action.event.item_name.lower()
    ]
    assert chicken
    chicken_event = next(
        (action.event for action in chicken if "weight_g=1200" in (action.event.note or "")),
        chicken[0].event,
    )
    chicken_note = chicken_event.note or ""
    assert "weight_g=1200" in chicken_note
    assert "use_by=9th" in chicken_note

    banned = {"total", "use by", "use-by", "best before", "cheers", "ignore"}
    for action in actions:
        assert not any(phrase in action.event.item_name.lower() for phrase in banned)


def test_inventory_agent_handles_milk_bread_stt():
    agent, _ = _make_agent()
    actions, _ = agent._parse_inventory_actions(STT_MILK_BREAD)
    assert actions

    bread = [action for action in actions if "bread" in action.event.item_name.lower()]
    assert bread
    assert any(action.event.quantity == 2 for action in bread)

    milk = [action for action in actions if "milk" in action.event.item_name.lower()]
    assert milk
    milk_note = milk[0].event.note or ""
    assert "volume_ml=2000" in milk_note
    assert "use_by=11th" in milk_note


def test_inventory_agent_dedupes_salmon_and_soy():
    agent, _ = _make_agent()
    stt = "Two salmon fillets, 360g total. One bottle of soy sauce, 150ml. Done."
    actions, _ = agent._parse_inventory_actions(stt)

    salmon_weight = [
        action
        for action in actions
        if "salmon" in action.event.item_name.lower()
        and "weight_g=360" in (action.event.note or "")
    ]
    assert salmon_weight

    soy_volume = [
        action
        for action in actions
        if "soy sauce" in action.event.item_name.lower()
        and "volume_ml=150" in (action.event.note or "")
    ]
    assert soy_volume

    assert len(actions) == 2, "Expected only salmon and soy sauce proposals."
    assert not any(
        action.event.item_name.strip().lower() in {"total", "done"} for action in actions
    )


def test_inventory_agent_handles_long_cupboard_fridge_message():
    agent, _ = _make_agent()
    actions, warnings = agent._parse_inventory_actions(STT_CUPBOARD_FRIDGE_LONG)
    assert actions, "Expected actions from the long cupboard/fridge STT message."

    chicken = [
        action for action in actions if "chicken thighs" in action.event.item_name.lower()
    ]
    assert chicken
    chicken_note = chicken[0].event.note or ""
    assert "weight_g=1200" in chicken_note
    assert "use_by=9th" in chicken_note

    eggs = [action for action in actions if "egg" in action.event.item_name.lower()]
    assert eggs
    egg_event = eggs[0].event
    assert egg_event.quantity == 6
    assert egg_event.unit == "count"

    bread = [action for action in actions if "bread" in action.event.item_name.lower()]
    assert bread
    assert any(action.event.quantity == 2 and action.event.unit == "count" for action in bread)

    milk = [action for action in actions if "milk" in action.event.item_name.lower()]
    assert milk
    milk_event = milk[0].event
    assert milk_event.unit == "ml"
    assert milk_event.quantity == 2000.0
    milk_note = milk_event.note or ""
    assert "volume_ml=2000" in milk_note
    assert "use_by=11th" in milk_note

    assert any(
        "orange juice" in action.event.item_name.lower() for action in actions
    ), "Orange juice should be parsed from the fridge clause."

    cereal = [action for action in actions if "cereal" in action.event.item_name.lower()]
    assert cereal, "Box of cereal should survive the uncertainty clause."

    cereal_note = cereal[0].event.note or ""
    assert "use_by" not in cereal_note

    eggs_note = egg_event.note or ""
    assert "use_by=11th" not in eggs_note

    bread_note = bread[0].event.note or ""
    assert "use_by=11th" not in bread_note

    banned = {"not sure", "maybe", "cheers", "ignore", "total", "use by"}
    for action in actions:
        assert not any(phrase in action.event.item_name.lower() for phrase in banned)



def test_inventory_agent_parses_number_words():
    agent, _ = _make_agent()
    action, _ = agent._parse_inventory_action("added three onions")
    assert action is not None
    assert action.event.quantity == 3


def test_inventory_agent_confirm_before_write(authed_client):
    thread = "inv-confirm"
    before = len(_inventory_events(authed_client))
    resp = authed_client.post(
        "/chat/inventory",
        json={"mode": "fill", "message": "bought 1 loaf", "thread_id": thread},
    )
    proposal_id = resp.json()["proposal_id"]
    assert len(_inventory_events(authed_client)) == before

    confirm = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread},
    )
    assert confirm.status_code == 200
    assert confirm.json()["applied"] is True
    assert len(_inventory_events(authed_client)) == before + len(resp.json()["proposed_actions"])


def test_inventory_agent_deny_is_non_destructive(authed_client):
    thread = "inv-deny"
    before = len(_inventory_events(authed_client))
    resp = authed_client.post(
        "/chat/inventory",
        json={"mode": "fill", "message": "added 2 carrots", "thread_id": thread},
    )
    proposal_id = resp.json()["proposal_id"]

    deny = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": False, "thread_id": thread},
    )
    assert deny.status_code == 200
    assert deny.json()["applied"] is False
    assert len(_inventory_events(authed_client)) == before


def test_inventory_agent_thread_scope(authed_client):
    thread_a = "inv-thread-a"
    thread_b = "inv-thread-b"
    resp = authed_client.post(
        "/chat/inventory",
        json={"mode": "fill", "message": "bought 4 apples", "thread_id": thread_a},
    )
    proposal_id = resp.json()["proposal_id"]
    wrong_thread = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread_b},
    )
    assert wrong_thread.status_code == 400
    assert len(_inventory_events(authed_client)) == 0

    ok = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread_a},
    )
    assert ok.status_code == 200
    assert ok.json()["applied"] is True
