from app.services.mealplan_store_service import get_mealplan_store_service


def test_chef_agent_requires_auth(client):
    resp = client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 5 days", "thread_id": "t-chef-1"},
    )
    assert resp.status_code == 401


def test_chef_agent_requires_thread_id(authed_client):
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 3 days"},
    )
    assert resp.status_code == 400


def test_chef_agent_requires_fill_mode(authed_client):
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "ask", "message": "plan for 3 days", "thread_id": "t-chef-2"},
    )
    assert resp.status_code == 400


def test_chef_agent_propose_and_confirm(authed_client):
    thread = "t-chef-plan"
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 5 days, 3 meals per day", "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    assert body["proposal_id"] is not None
    proposal_id = body["proposal_id"]
    assert len(body["proposed_actions"]) == 1
    action = body["proposed_actions"][0]
    assert action["action_type"] == "generate_mealplan"
    plan = action["mealplan"]
    # Multi-day: 5 days as requested
    assert len(plan["days"]) == 5
    for day in plan["days"]:
        assert len(day["meals"]) == 3

    # Confirm
    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": True, "thread_id": thread},
    )
    assert resp.status_code == 200
    confirm_body = resp.json()
    assert confirm_body["applied"] is True
    assert len(confirm_body["applied_event_ids"]) == 1
    assert confirm_body["applied_event_ids"][0] == plan["plan_id"]
    latest = get_mealplan_store_service().get_latest_plan("test-user")
    assert latest is not None
    assert latest.plan_id == plan["plan_id"]


def test_chef_agent_propose_and_decline(authed_client):
    thread = "t-chef-decline"
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 2 days, 2 meals per day", "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    # Multi-day: 2 days as requested
    assert len(body["proposed_actions"][0]["mealplan"]["days"]) == 2
    proposal_id = body["proposal_id"]

    # Decline
    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": proposal_id, "confirm": False, "thread_id": thread},
    )
    assert resp.status_code == 200
    assert resp.json()["applied"] is False


def test_chef_agent_defaults_when_no_params(authed_client):
    """When message has no explicit days/meals, prefs defaults should be used (capped to 1 day)."""
    thread = "t-chef-defaults"
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "make me a meal plan", "thread_id": thread},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    action = body["proposed_actions"][0]
    plan = action["mealplan"]
    # Default plan_days=7 from prefs, meals_per_day=3 from prefs
    assert len(plan["days"]) == 7
    for day in plan["days"]:
        assert len(day["meals"]) == 3


def test_chef_agent_thread_isolation(authed_client):
    """Proposals from different threads don't interfere."""
    thread_a = "t-chef-iso-a"
    thread_b = "t-chef-iso-b"

    resp_a = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 2 days", "thread_id": thread_a},
    )
    resp_b = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 4 days", "thread_id": thread_b},
    )
    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    # Multi-day: 2 and 4 days as requested
    assert len(resp_a.json()["proposed_actions"][0]["mealplan"]["days"]) == 2
    assert len(resp_b.json()["proposed_actions"][0]["mealplan"]["days"]) == 4

    pid_a = resp_a.json()["proposal_id"]
    pid_b = resp_b.json()["proposal_id"]
    assert pid_a != pid_b

    # Confirm A with thread B should fail (proposal not found for wrong thread)
    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": pid_a, "confirm": True, "thread_id": thread_b},
    )
    assert resp.status_code == 400

    # Confirm A with correct thread
    resp = authed_client.post(
        "/chat/confirm",
        json={"proposal_id": pid_a, "confirm": True, "thread_id": thread_a},
    )
    assert resp.status_code == 200
    assert resp.json()["applied"] is True


def test_chef_agent_multiday_cap_at_7(authed_client):
    """Requesting more than 7 days is capped at 7."""
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan for 14 days", "thread_id": "t-cap"},
    )
    assert resp.status_code == 200
    body = resp.json()
    plan = body["proposed_actions"][0]["mealplan"]
    assert len(plan["days"]) == 7
    assert "7-day" in body["reply_text"]


def test_chef_agent_prefs_allergy_filter(authed_client):
    """Recipes with ingredients matching allergy keywords are excluded."""
    # Set prefs with chicken allergy (should exclude Garlic Butter Chicken)
    authed_client.put("/prefs", json={"prefs": {
        "allergies": ["chicken"],
        "dislikes": [],
        "cuisine_likes": [],
        "servings": 2,
        "meals_per_day": 3,
    }})
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "make a plan", "thread_id": "t-allergy"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is True
    plan = body["proposed_actions"][0]["mealplan"]
    for day in plan["days"]:
        for meal in day["meals"]:
            assert "chicken" not in meal["name"].lower()


def test_chef_agent_all_recipes_excluded(authed_client):
    """When all recipes are excluded by prefs, graceful message returned."""
    authed_client.put("/prefs", json={"prefs": {
        "allergies": ["tomato", "chicken", "veggies"],
        "dislikes": [],
        "cuisine_likes": [],
        "servings": 2,
        "meals_per_day": 3,
    }})
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "plan please", "thread_id": "t-excluded"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["confirmation_required"] is False
    assert "conflict" in body["reply_text"].lower() or "allergies" in body["reply_text"].lower()


def test_chef_agent_inventory_notes(authed_client):
    """Plan notes mention in-stock items when inventory has matching ingredients."""
    # Add tomato to inventory
    authed_client.post("/inventory/events", json={
        "event_type": "add",
        "item_name": "tomato",
        "quantity": 5,
        "unit": "count",
        "location": "pantry",
    })
    resp = authed_client.post(
        "/chat/mealplan",
        json={"mode": "fill", "message": "make a plan", "thread_id": "t-inv-notes"},
    )
    assert resp.status_code == 200
    body = resp.json()
    plan = body["proposed_actions"][0]["mealplan"]
    notes = plan.get("notes", "")
    assert "tomato" in notes.lower()


def test_general_chat_mealplan_nudge_ask(authed_client):
    """ASK mode on /chat returns nudge when message mentions meal plan."""
    resp = authed_client.post(
        "/chat",
        json={"mode": "ask", "message": "make me a meal plan"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "meal plan flow" in body["reply_text"].lower()
    assert body["confirmation_required"] is False


def test_general_chat_mealplan_nudge_fill(authed_client):
    """FILL mode on /chat returns nudge when message mentions meal plan."""
    resp = authed_client.post(
        "/chat",
        json={"mode": "fill", "message": "plan my meals", "thread_id": "t-nudge-fill"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "meal plan flow" in body["reply_text"].lower()
    assert body["confirmation_required"] is False
