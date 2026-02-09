import re

from app.schemas import ChatRequest, UserMe
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
    actions, _, _ = agent._parse_inventory_actions(STT_INVENTORY_MESSAGE)
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
    actions, _, _ = agent._parse_inventory_actions(STT_CONTAINER_SCAN)
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
    actions, _, _ = agent._parse_inventory_actions(STT_CHICKEN_USE_BY)
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
    actions, _, _ = agent._parse_inventory_actions(STT_MILK_BREAD)
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
    actions, _, _ = agent._parse_inventory_actions(stt)

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
    actions, warnings, _ = agent._parse_inventory_actions(STT_CUPBOARD_FRIDGE_LONG)
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
    # A1: "box" must not leak into the item name
    assert "box" not in cereal[0].event.item_name.lower(), (
        f"Container word 'box' leaked into cereal name: {cereal[0].event.item_name}"
    )

    eggs_note = egg_event.note or ""
    assert "use_by=11th" not in eggs_note

    bread_note = bread[0].event.note or ""
    assert "use_by=11th" not in bread_note

    # A5+A6: flour should survive uncertainty splitting
    flour = [a for a in actions if "flour" in a.event.item_name.lower()]
    assert flour, "Flour should be parsed despite 'Not sure how much' phrasing."

    # Frozen peas should appear exactly once
    peas = [a for a in actions if "peas" in a.event.item_name.lower()]
    assert len(peas) == 1, f"Expected 1 frozen peas action, got {len(peas)}: {[a.event.item_name for a in peas]}"

    banned = {"not sure", "maybe", "cheers", "ignore", "total", "use by", "i've got"}
    for action in actions:
        assert not any(phrase in action.event.item_name.lower() for phrase in banned), (
            f"Banned phrase leaked into item name: {action.event.item_name}"
        )



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


# ---------------------------------------------------------------------------
# Fix 1: section-transition boundary prevents cross-section glue
# ---------------------------------------------------------------------------
def test_section_transition_splits_milk_from_cereal():
    """Now fridge stuff must act as a hard boundary; milk must not glue to cereal."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "Coco Pops one box quarter full. Now fridge stuff milk two litres"
    )
    names = {a.event.item_name.lower() for a in actions}
    # milk must be its own item
    assert any("milk" in n for n in names), f"Expected 'milk' in {names}"
    # no glued name containing both cereal and milk
    assert not any(
        "coco pops" in n and "milk" in n for n in names
    ), f"Glued cereal+milk name found: {names}"
    # location/transition words must not leak into item names
    assert not any("fridge" in n for n in names), f"'fridge' leaked into names: {names}"
    assert not any(n == "stuff" for n in names), f"'stuff' leaked as item: {names}"


# ---------------------------------------------------------------------------
# Fix 2: apostrophe-less STT chatter stripped from item names
# ---------------------------------------------------------------------------
def test_apostrophe_less_stt_filler_stripped():
    """STT 'I ve got' (without apostrophe) must be stripped so item is 'pasta'."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "I ve got pasta two 500 gram packs"
    )
    assert actions, "Expected at least one action."
    pasta = [a for a in actions if "pasta" in a.event.item_name.lower()]
    assert pasta, f"Expected a pasta action, got {[a.event.item_name for a in actions]}"
    assert pasta[0].event.item_name.lower().strip() == "pasta"


# ---------------------------------------------------------------------------
# Fix 3: bare filler words stripped as tokens within compound names
# ---------------------------------------------------------------------------
def test_unopened_stripped_from_item_name():
    """'unopened' must be stripped from compound names; 'chips' not 'unopened chips'."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "Mixed veg one bag unopened. Chips one bag third left"
    )
    names = {a.event.item_name.lower() for a in actions}
    assert any("chip" in n for n in names), f"Expected chips item, got {names}"
    assert "unopened chips" not in names, f"'unopened' leaked into chips name: {names}"
    assert any("mixed veg" in n for n in names), f"Expected mixed veg item, got {names}"


# ---------------------------------------------------------------------------
# Fraction / "half left" normalization tests
# ---------------------------------------------------------------------------
def test_fraction_compute_milk_half_left():
    """Base amount exists (2 litres) + 'half left' → remaining=1000ml in note."""
    agent, _ = _make_agent()
    actions, warnings, _ = agent._parse_inventory_actions(
        "milk two litres half left"
    )
    milk = [a for a in actions if "milk" in a.event.item_name.lower()]
    assert milk, f"Expected milk action, got {[a.event.item_name for a in actions]}"
    milk_event = milk[0].event
    assert milk_event.item_name.lower().strip() == "milk"
    assert milk_event.quantity == 2000.0
    assert milk_event.unit == "ml"
    assert "remaining=1000ml" in (milk_event.note or ""), (
        f"Expected remaining=1000ml in note, got: {milk_event.note}"
    )
    assert "FALLBACK_MISSING_QUANTITY" not in warnings


def test_fraction_no_compute_chips_quarter_full():
    """No base in g/ml (count only) + 'quarter full' → remaining=quarter in note."""
    agent, _ = _make_agent()
    actions, warnings, _ = agent._parse_inventory_actions(
        "Chips one bag quarter full"
    )
    chips = [a for a in actions if "chip" in a.event.item_name.lower()]
    assert chips, f"Expected chips action, got {[a.event.item_name for a in actions]}"
    chips_event = chips[0].event
    assert "remaining=quarter" in (chips_event.note or ""), (
        f"Expected remaining=quarter in note, got: {chips_event.note}"
    )
    assert "FALLBACK_MISSING_QUANTITY" not in warnings


def test_fraction_preserves_full_fat_milk():
    """'full fat milk' must NOT trigger fraction stripping; name stays intact."""
    agent, _ = _make_agent()
    actions, warnings, _ = agent._parse_inventory_actions(
        "full fat milk two litres"
    )
    milk = [a for a in actions if "milk" in a.event.item_name.lower()]
    assert milk, f"Expected milk action, got {[a.event.item_name for a in actions]}"
    milk_name = milk[0].event.item_name.lower()
    assert "full" in milk_name or "fat" in milk_name, (
        f"Expected 'full fat' preserved in name, got: {milk_name}"
    )
    # No spurious fraction note
    assert "remaining=" not in (milk[0].event.note or ""), (
        f"Unexpected remaining note on full fat milk: {milk[0].event.note}"
    )


def test_fraction_compute_peas_third_left():
    """Peas 900g + 'third left' → remaining=300g."""
    agent, _ = _make_agent()
    actions, warnings, _ = agent._parse_inventory_actions(
        "peas 900 grams third left"
    )
    peas = [a for a in actions if "pea" in a.event.item_name.lower()]
    assert peas, f"Expected peas action, got {[a.event.item_name for a in actions]}"
    peas_note = peas[0].event.note or ""
    assert "remaining=300g" in peas_note, (
        f"Expected remaining=300g in note, got: {peas_note}"
    )


# ---------------------------------------------------------------------------
# Bug-fix: _looks_like_date_quantity must respect sentence boundaries
# ---------------------------------------------------------------------------
STT_PANTRY_SCAN_FULL = (
    "Alright Little Chef quick pantry scan: Pasta two 500 gram packs both unopened. "
    "Rice one kilo bag about half left. Tinned chopped tomatoes six tins best before 10 October. "
    "Tuna four tins best before 3 March. Baked beans five tins best before 20 January. "
    "Chickpeas three tins best before 12 May. Peas 900 gram bag half left. "
    "Mince beef 500 grams use by 10 February. Spinach one bag half left use by 8 February."
)


def test_date_qty_does_not_swallow_items_across_sentences():
    """Items after date expressions must not be treated as date quantities."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(STT_PANTRY_SCAN_FULL)
    names = {a.event.item_name.lower() for a in actions}
    for expected in ("tuna", "peas", "spinach"):
        assert any(expected in n for n in names), (
            f"Expected '{expected}' in actions, got {names}"
        )
    assert len(actions) >= 9, f"Expected >=9 actions, got {len(actions)}: {names}"


def test_date_qty_still_filters_real_date_numbers():
    """Numbers inside date expressions (e.g. '10' in 'best before 10 October') must still be skipped."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "Tuna four tins best before 3 March."
    )
    names = {a.event.item_name.lower() for a in actions}
    # Should produce one action for tuna, not one for '3'
    assert any("tuna" in n for n in names), f"Expected tuna, got {names}"
    assert len(actions) == 1, f"Expected exactly 1 action (tuna), got {len(actions)}: {names}"


# ---------------------------------------------------------------------------
# Bug-fix: "Alright Little Chef" must not leak as an item name
# ---------------------------------------------------------------------------
def test_alright_little_chef_not_an_item():
    """Greeting variants must be stripped; 'little chef' never becomes an item."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "Alright Little Chef I've got pasta two packs"
    )
    names = {a.event.item_name.lower() for a in actions}
    assert not any("little chef" in n for n in names), (
        f"'little chef' leaked as item name: {names}"
    )
    assert any("pasta" in n for n in names), f"Expected pasta, got {names}"


def test_okay_little_chef_not_an_item():
    """'Okay Little Chef' greeting also must not leak."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "Okay Little Chef quick stock check: eggs six"
    )
    names = {a.event.item_name.lower() for a in actions}
    assert not any("little chef" in n for n in names), (
        f"'little chef' leaked as item name: {names}"
    )
    assert any("egg" in n for n in names), f"Expected eggs, got {names}"


# ---------------------------------------------------------------------------
# Bug-fix: "both" must not become an inventory item
# ---------------------------------------------------------------------------
def test_both_not_an_item():
    """'both' from 'two 500 gram packs both unopened' must not produce an action."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "Pasta two 500 gram packs both unopened"
    )
    names = {a.event.item_name.lower() for a in actions}
    assert "both" not in names, f"'both' leaked as item name: {names}"
    assert any("pasta" in n for n in names), f"Expected pasta, got {names}"


# ---------------------------------------------------------------------------
# Bug-fix: "quick pantry scan" must be stripped as a lead prefix
# ---------------------------------------------------------------------------
def test_quick_pantry_scan_stripped():
    """'quick pantry scan' must not appear in item names."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "quick pantry scan: Pasta two 500 gram packs"
    )
    names = {a.event.item_name.lower() for a in actions}
    assert not any("scan" in n for n in names), f"'scan' leaked: {names}"
    assert not any("pantry" in n for n in names), f"'pantry' leaked: {names}"
    assert any("pasta" in n for n in names), f"Expected pasta, got {names}"


# ---------------------------------------------------------------------------
# Full pantry scan: intro stripping + date capture + N-left + all items
# ---------------------------------------------------------------------------
STT_FULL_PANTRY = (
    "Alright Little Chef, quick pantry scan: I've got pasta two 500 gram packs both "
    "unopened, and rice one kilo bag about quarter left. Chopped tomatoes six tins best "
    "before 10 October. Tuna four tins best before 3 March. Now fridge stuff: milk two "
    "litres half left use by 10 February, Greek yoghurt two pots use by 11 February, "
    "cheddar cheese 400 grams about half left use by 14 February, ham one pack half left "
    "use by 9 February, spinach one bag half left use by 8 February, eggs six pack four "
    "left best before 12 February. And freezer: peas 900 grams third left, chicken "
    "nuggets one bag quarter full, chips one bag quarter full, bread one loaf about half left."
)


def test_full_pantry_scan_all_items_found():
    """All 14 items from a real-world STT must be parsed with zero junk."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(STT_FULL_PANTRY)
    names = {a.event.item_name.lower() for a in actions}
    for expected in (
        "pasta", "rice", "chopped tomatoes", "tuna", "milk",
        "greek yoghurt", "cheddar cheese", "ham", "spinach", "eggs",
        "peas", "chicken nuggets", "chips", "bread",
    ):
        assert any(expected in n for n in names), (
            f"Expected '{expected}' in actions, got {names}"
        )
    assert len(actions) == 14, f"Expected 14 actions, got {len(actions)}: {names}"


def test_full_pantry_scan_intro_stripped():
    """Greeting + prefix must not corrupt the first item name."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(STT_FULL_PANTRY)
    pasta = [a for a in actions if "pasta" in a.event.item_name.lower()]
    assert pasta, "Expected pasta action"
    name = pasta[0].event.item_name.lower()
    assert "scan" not in name, f"'scan' leaked into pasta name: {name}"
    assert "got" not in name, f"'got' leaked into pasta name: {name}"
    assert "pantry" not in name, f"'pantry' leaked into pasta name: {name}"


def test_date_capture_use_by_dd_month():
    """'use by 10 February' must appear in the note as date=10 February."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "milk two litres half left use by 10 February"
    )
    milk = [a for a in actions if "milk" in a.event.item_name.lower()]
    assert milk, "Expected milk action"
    note = milk[0].event.note or ""
    assert "date=10 February" in note, f"Expected date=10 February in note, got: {note}"


def test_date_capture_best_before_dd_month():
    """'best before 3 March' must appear in the note as date=3 March."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "Tuna four tins best before 3 March"
    )
    tuna = [a for a in actions if "tuna" in a.event.item_name.lower()]
    assert tuna, "Expected tuna action"
    note = tuna[0].event.note or ""
    assert "date=3 March" in note, f"Expected date=3 March in note, got: {note}"


def test_n_left_remaining_eggs():
    """'eggs six pack four left' must produce eggs qty=6 with remaining=4."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "eggs six pack four left best before 12 February"
    )
    eggs = [a for a in actions if "egg" in a.event.item_name.lower()]
    assert eggs, "Expected eggs action"
    egg = eggs[0].event
    assert egg.quantity == 6.0, f"Expected qty=6, got {egg.quantity}"
    note = egg.note or ""
    assert "remaining=4" in note, f"Expected remaining=4 in note, got: {note}"


def test_smart_apostrophe_normalized():
    """Curly apostrophe \u2019 must be normalized so 'I\u2019ve got' is stripped."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(
        "I\u2019ve got pasta two 500 gram packs"
    )
    assert actions, "Expected at least one action"
    pasta = [a for a in actions if "pasta" in a.event.item_name.lower()]
    assert pasta, f"Expected pasta, got {[a.event.item_name for a in actions]}"
    assert pasta[0].event.item_name.lower().strip() == "pasta"


# ---------------------------------------------------------------------------
# Full 21-item scan: realistic STT with cupboard / fridge / freezer sections
# ---------------------------------------------------------------------------
STT_FULL_SCAN_21 = (
    "Okay Little Chef, full scan again: cupboard first, pasta three packs 500 grams, "
    "one pack opened and about half left, rice one kilo bag about a third left, lentils "
    "500 grams about quarter left, chopped tomatoes eight tins best before 12 October, "
    "tuna six tins best before 5 March, baked beans four tins best before 20 January, "
    "peanut butter one jar half left best before 6 June, olive oil 500 ml bottle quarter "
    "left. Now fridge stuff: milk two litres half left use by 10 February, cheddar cheese "
    "400 grams about half left use by 14 February, Greek yoghurt three pots use by 11 "
    "February, butter 250 grams half left best before 2 March, eggs ten pack six left "
    "best before 12 February, spinach one bag half left use by 8 February, chicken "
    "breast two pieces use by 9 February, mince beef 500 grams use by 10 February. And "
    "freezer: peas 900 grams third left, mixed veg one bag unopened, chips one bag "
    "quarter full, bread one loaf about half left, ice cream one tub half full."
)

_EXPECTED_21 = [
    "pasta", "rice", "lentils", "chopped tomatoes", "tuna", "baked beans",
    "peanut butter", "olive oil", "milk", "cheddar cheese", "greek yoghurt",
    "butter", "eggs", "spinach", "chicken breast", "mince beef",
    "peas", "mixed veg", "chips", "bread", "ice cream",
]


def test_full_scan_21_all_items_found():
    """All 21 items from the hardest real-world STT must parse with zero junk."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(STT_FULL_SCAN_21)
    names = {a.event.item_name.lower() for a in actions}
    for expected in _EXPECTED_21:
        assert any(expected in n for n in names), (
            f"Expected '{expected}' in actions, got {sorted(names)}"
        )
    # No junk: action count must equal expected count
    assert len(actions) == len(_EXPECTED_21), (
        f"Expected {len(_EXPECTED_21)} actions, got {len(actions)}: {sorted(names)}"
    )


def test_full_scan_21_dates_assigned():
    """Items with explicit dates must have correct date in note."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(STT_FULL_SCAN_21)
    expected_dates = {
        "chopped tomatoes": "12 October",
        "tuna": "5 March",
        "baked beans": "20 January",
        "peanut butter": "6 June",
        "milk": "10 February",
        "cheddar cheese": "14 February",
        "greek yoghurt": "11 February",
        "butter": "2 March",
        "eggs": "12 February",
        "spinach": "8 February",
        "chicken breast": "9 February",
        "mince beef": "10 February",
    }
    def _find(key):
        """Exact match first, then substring — avoids 'butter' matching 'peanut butter'."""
        exact = [a for a in actions if a.event.item_name.lower().strip() == key]
        if exact:
            return exact[0]
        partial = [a for a in actions if key in a.event.item_name.lower()]
        return partial[0] if partial else None

    for item_key, expected_date in expected_dates.items():
        hit = _find(item_key)
        assert hit, f"Missing action for '{item_key}'"
        note = hit.event.note or ""
        assert f"date={expected_date}" in note, (
            f"'{item_key}' should have date={expected_date}, got note='{note}'"
        )


def test_full_scan_21_no_date_bleed():
    """Items without dates must NOT have a date in their note."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(STT_FULL_SCAN_21)
    no_date_items = {"pasta", "rice", "lentils", "olive oil", "peas",
                     "mixed veg", "chips", "bread", "ice cream"}
    for a in actions:
        name = a.event.item_name.lower()
        if any(nd in name for nd in no_date_items):
            note = a.event.note or ""
            assert "date=" not in note, (
                f"'{name}' should NOT have a date, got note='{note}'"
            )


def test_full_scan_21_eggs_date_and_remaining():
    """Eggs: 'ten pack six left best before 12 February' → remaining=6 + date=12 February."""
    agent, _ = _make_agent()
    actions, _, _ = agent._parse_inventory_actions(STT_FULL_SCAN_21)
    eggs = [a for a in actions if "egg" in a.event.item_name.lower()]
    assert eggs, "Expected eggs action"
    note = eggs[0].event.note or ""
    assert "remaining=6" in note, f"Expected remaining=6 in note, got: {note}"
    assert "date=12 February" in note, f"Expected date=12 February in note, got: {note}"


STT_CUPBOARD_PARAGRAPH = (
    "I'm at the cupboard now. I've got two loaves of bread, one carton of eggs, "
    "a two litre bottle of milk, and about 500 grams of pasta. There's one kilo of "
    "basmati rice, three tins of chopped tomatoes, two tins of tuna, one jar of peanut "
    "butter, and a bottle of olive oil about 500 ml. I've also got a box of cereal. "
    "Not sure how much flour is left, maybe half a bag, and in the freezer I've got "
    "frozen peas, roughly 900 grams."
)


def test_stt_cupboard_paragraph_no_garbage():
    """Regression: the STT paragraph should not produce garbage names or miss flour."""
    agent, _ = _make_agent()
    actions, warnings, follow_ups = agent._parse_inventory_actions(STT_CUPBOARD_PARAGRAPH)
    names = [a.event.item_name.lower() for a in actions]

    # Flour must appear
    assert any("flour" in n for n in names), f"Flour missing from parsed items: {names}"

    # Cereal must not be prefixed with 'box'
    cereal = [n for n in names if "cereal" in n]
    assert cereal, f"Cereal missing: {names}"
    assert all("box" not in n for n in cereal), f"Container word 'box' leaked: {cereal}"

    # No garbage item names containing chatter
    garbage = {"i've", "i ve", "got", "roughly", "in i"}
    for n in names:
        assert not any(g in n for g in garbage), f"Garbage leaked into item name: {n}"

    # Frozen peas should appear exactly once
    peas = [n for n in names if "peas" in n]
    assert len(peas) == 1, f"Expected 1 peas entry, got {len(peas)}: {peas}"

    # FALLBACK_MISSING_QUANTITY should not fire for clean parses
    assert "FALLBACK_MISSING_QUANTITY" not in warnings or any(
        a.event.unit == "count" and a.event.quantity == 1.0
        and not any(kw in a.event.item_name.lower() for kw in garbage)
        for a in actions
    )


def test_ambiguity_follow_up_eggs_carton():
    """When eggs are given as a container qty, a follow-up question should be generated."""
    agent, _ = _make_agent()
    _actions, _warnings, follow_ups = agent._parse_inventory_actions(
        "one carton of eggs"
    )
    assert follow_ups, "Expected an ambiguity follow-up for 'one carton of eggs'"
    assert any("eggs" in q and "carton" in q for q in follow_ups), (
        f"Follow-up should mention eggs and carton: {follow_ups}"
    )


def test_ambiguity_follow_up_not_triggered_for_plain_eggs():
    """Direct egg count (e.g. '6 eggs') should NOT trigger ambiguity follow-up."""
    agent, _ = _make_agent()
    _actions, _warnings, follow_ups = agent._parse_inventory_actions("6 eggs")
    assert not follow_ups, f"No follow-up expected for plain eggs: {follow_ups}"


def test_parser_path_edit_merges_into_existing_proposal():
    """When initial proposal came from the parser path (empty raw_items),
    typing an edit like 'I have four eggs' should merge rather than fail."""
    agent, _ = _make_agent()
    user = UserMe(
        user_id="u1", email="t@t.com", onboarded=True, provider_subject="s1"
    )
    # Step 1: initial inventory input
    req1 = ChatRequest(
        message="one carton of eggs, two loaves of bread",
        mode="fill",
        thread_id="th-edit-test",
    )
    resp1 = agent.handle_fill(user, req1)
    assert resp1.confirmation_required
    assert resp1.proposal_id
    initial_actions = {a.event.item_name.lower(): a.event.quantity for a in resp1.proposed_actions}
    assert initial_actions.get("eggs") == 1.0
    assert initial_actions.get("bread") == 2.0

    # Step 2: edit to clarify eggs
    req2 = ChatRequest(
        message="I have four eggs",
        mode="fill",
        thread_id="th-edit-test",
    )
    resp2 = agent.handle_fill(user, req2)
    assert resp2.confirmation_required
    assert resp2.proposal_id == resp1.proposal_id, "Should reuse same proposal"
    edited_actions = {a.event.item_name.lower(): a.event.quantity for a in resp2.proposed_actions}
    assert edited_actions.get("eggs") == 4.0, (
        f"Expected eggs updated to 4, got {edited_actions.get('eggs')}"
    )
    assert edited_actions.get("bread") == 2.0, "Bread should be preserved"
